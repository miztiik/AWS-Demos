import os
import simplejson

from datetime import datetime, timedelta
from uuid import uuid4

from django.conf import settings

import boto

from celery.decorators import task
from celery.task import PeriodicTask

from pdf.models import Document


BOOTSTRAP_SCRIPT = """#!/bin/bash
apt-get update
apt-get install -y imagemagick

python -c "import os
import json

from datetime import datetime
from subprocess import Popen, PIPE
from time import sleep
from uuid import uuid4

import boto

KEY = '%(KEY)s'
SECRET = '%(SECRET)s'

request_queue = boto.connect_sqs(KEY, SECRET).create_queue('%(REQUEST_QUEUE)s')
response_queue = boto.connect_sqs(KEY, SECRET).create_queue('%(RESPONSE_QUEUE)s')
count = 0


def read_json_pointer_message():
    m = request_queue.read(3600) # Give the job an hour to run, plenty of time to avoid double-runs
    if m is not None:
        pointer = json.loads(m.get_body())
        k = boto.connect_s3(KEY, SECRET).get_bucket(pointer['bucket']).get_key(pointer['key'])
        data = json.loads(k.get_contents_as_string())
        data['pointer'] = m
        return data

def delete_json_pointer_message(data):
    request_queue.delete_message(data['pointer'])

def write_json_pointer_message(data, bucket, key_name, base_key):
    b = boto.connect_s3(KEY, SECRET).get_bucket(bucket)
    k = b.new_key(base_key.replace(os.path.basename(base_key), key_name))
    k.set_contents_from_string(json.dumps(data))
    response_message = {'bucket': b.name, 'key': k.name}
    message = response_queue.new_message(body=json.dumps(response_message))
    response_queue.write(message)

def download(bucket, key, local_file):
    b = boto.connect_s3(KEY, SECRET).get_bucket(bucket)
    k = b.get_key(key)
    k.get_contents_to_filename(local_file)

def upload_file(local_file, bucket, key, public=False):
    b = boto.connect_s3(KEY, SECRET).get_bucket(bucket)
    k = b.new_key(key)
    k.set_contents_from_filename(local_file)
    if public:
        k.set_acl('public-read')

def get_tstamp():
    return datetime.utcnow().isoformat(' ').split('.')[0]


while True:
    request_data = read_json_pointer_message()
    start = get_tstamp()
    if request_data is None:
        count += 1
        if count > 10:
            break
        else:
            sleep(5)
    else:
        RUN_ID = str(uuid4())
        WORKING_PATH = '/mnt/' + RUN_ID
        try:
            os.makedirs(WORKING_PATH)
        except:
            pass
        count = 0
        try:
            try:
                bname = request_data['bucket']
                kname = request_data['key']
                doc_uuid = request_data['uuid']
                local_filename = os.path.join(WORKING_PATH, os.path.basename(kname))
                output = os.path.join(WORKING_PATH, 'page.png')
                cmd = 'convert -density 400 ' + local_filename + ' ' + output

                start_data = {'status': 'P', 'uuid': doc_uuid, 'now': start}
                write_json_pointer_message(start_data, bucket=bname, key_name='start.json', base_key=kname)
                download(bname, kname, local_filename)
                p = Popen(cmd.split(), stdout=PIPE, stderr=PIPE)
                rc = p.wait()
                images = [f for f in os.listdir(WORKING_PATH) if f.endswith('png')]
                for image in images:
                    new_key_name = kname.replace(os.path.basename(kname), image)
                    local_image = os.path.join(WORKING_PATH, image)
                    upload_file(local_image, bname, new_key_name, public=True)
                data = {'status': 'F', 'uuid': doc_uuid, 'pages': len(images), 'now': get_tstamp()}
                write_json_pointer_message(data, bucket=bname, key_name='results.json', base_key=kname)
            except:
                import sys, traceback
                exc_type, exc_value, exc_traceback = sys.exc_info()
                e = traceback.format_exception(exc_type, exc_value, exc_traceback)
                e = ''.join(e)
                data = {'status': 'E', 'uuid': doc_uuid, 'exception': str(e), 'now': get_tstamp()}
                write_json_pointer_message(data, bucket=bname, key_name='error.json', base_key=kname)
        except Exception, e:
            pass
        delete_json_pointer_message(request_data)
"

/sbin/shutdown now -h
"""


REQUEST_QUEUE = getattr(settings, "PDF_REQUEST_QUEUE", "pdf_requests")
RESPONSE_QUEUE = getattr(settings, "PDF_RESPONSE_QUEUE", "pdf_responses")
ACL = getattr(settings, "PDF_AWS_ACL", "public-read")
AMI_ID = getattr(settings, "PDF_AMI_ID", "ami-bb709dd2")
KEYPAIR = getattr(settings, "PDF_KEYPAIR_NAME", None)
MAX_INSTANCES = getattr(settings, 'PDF_MAX_NODES', 20)
SECURITY_GROUPS = getattr(settings, 'PDF_SECURITY_GROUPS', None)


def queue_json_message(doc, doc_key):
    key_name = doc_key.name.replace(os.path.basename(doc_key.name), "message-%s.json" % str(uuid4()))
    key = doc_key.bucket.new_key(key_name)
    message_data = simplejson.dumps({'bucket': doc_key.bucket.name, 'key': doc_key.name, 'uuid': doc.uuid})
    key.set_contents_from_string(message_data)
    msg_body = {'bucket': key.bucket.name, 'key': key.name}
    queue = boto.connect_sqs(settings.PDF_AWS_KEY, settings.PDF_AWS_SECRET).create_queue(REQUEST_QUEUE)
    msg = queue.new_message(body=simplejson.dumps(msg_body))
    queue.write(msg)


def upload_file_to_s3(doc):
    file_path = doc.local_document.path
    b = boto.connect_s3(settings.PDF_AWS_KEY, settings.PDF_AWS_SECRET).get_bucket(settings.PDF_UPLOAD_BUCKET)
    name = '%s/%s' % (doc.uuid, os.path.basename(file_path))
    k = b.new_key(name)
    k.set_contents_from_filename(file_path)
    k.set_acl(ACL)
    return k


@task
def process_file(doc):
    """Transfer uploaded file to S3 and queue up message to process PDF."""
    key = upload_file_to_s3(doc)
    doc.remote_document = "http://%s.s3.amazonaws.com/%s" % (key.bucket.name, key.name)
    doc.date_stored = datetime.utcnow()
    doc.status = 'S'
    doc.save()

    queue_json_message(doc, key)
    doc.status = 'Q'
    doc.date_queued = datetime.utcnow()
    doc.save()

    return True


class CheckResponseQueueTask(PeriodicTask):
    """
    Checks response queue for messages returned from running processes in the
    cloud.  The messages are read and corresponding `pdf.models.Document`
    records are updated.
    """
    run_every = timedelta(seconds=30)

    def _dequeue_json_message(self):
        sqs = boto.connect_sqs(settings.PDF_AWS_KEY, settings.PDF_AWS_SECRET)
        queue = sqs.create_queue(RESPONSE_QUEUE)
        msg = queue.read()
        if msg is not None:
            data = simplejson.loads(msg.get_body())
            bucket = data.get('bucket', None)
            key = data.get("key", None)
            queue.delete_message(msg)
            if bucket is not None and key is not None:
                return data

    def run(self, **kwargs):
        logger = self.get_logger(**kwargs)
        logger.info("Running periodic task!")
        data = self._dequeue_json_message()
        if data is not None:
            Document.process_response(data)
            return True
        return False


class CheckQueueLevelsTask(PeriodicTask):
    """
    Checks the number of messages in the queue and compares it with the number
    of instances running, only booting nodes if the number of queued messages
    exceed the number of nodes running.
    """
    run_every = timedelta(seconds=60)

    def run(self, **kwargs):
        ec2 = boto.connect_ec2(settings.PDF_AWS_KEY, settings.PDF_AWS_SECRET)
        sqs = boto.connect_sqs(settings.PDF_AWS_KEY, settings.PDF_AWS_SECRET)

        queue = sqs.create_queue(REQUEST_QUEUE)
        num = queue.count()
        launched = 0
        icount = 0

        reservations = ec2.get_all_instances()
        for reservation in reservations:
            for instance in reservation.instances:
                if instance.state == "running" and instance.image_id == AMI_ID:
                    icount += 1
        to_boot = min(num - icount, MAX_INSTANCES)

        if to_boot > 0:
            startup = BOOTSTRAP_SCRIPT % {
                'KEY': settings.PDF_AWS_KEY,
                'SECRET': settings.PDF_AWS_SECRET,
                'RESPONSE_QUEUE': RESPONSE_QUEUE,
                'REQUEST_QUEUE': REQUEST_QUEUE}
            r = ec2.run_instances(
                image_id=AMI_ID,
                min_count=to_boot,
                max_count=to_boot,
                key_name=KEYPAIR,
                security_groups=SECURITY_GROUPS,
                user_data=startup)
            launched = len(r.instances)
        return launched