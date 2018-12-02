# Scaling ElasticSearch Domain Cluster
Lets say you are running ES Cluster and you want to downscale your cluster after analyzing your utiliztaion, how do we do that. Say for example, we want to move from M4 instance types to T2 instance types to save on costs. In this post, we see how to do that through CLI. You can automate this through Lambda to automatically upscale your cluster if you predict a higher data coming through.

_For information about which instance type is appropriate for your use case, see [Sizing Amazon ES Domains](https://docs.aws.amazon.com/elasticsearch-service/latest/developerguide/sizing-domains.html)._

![Scaling ElasticSearch Domain Cluster Valaxy Miztiik](https://raw.githubusercontent.com/miztiik/AWS-Demos/master/How-To/setup-scaling-elasticsearch/images/scaling-elasticsearch-miztiik-valaxy.png)

### Get current config
We can use the describe option in the CLI to get the curent configuration.
```sh
# aws es describe-elasticsearch-domain --domain-name <VALUE>
# or
# aws es describe-elasticsearch-domain-config --domain-name <VALUE>

aws es describe-elasticsearch-domain-config --domain-name s3-log-ingester-pub
```
The expected output should be something like this,
```json
{
    "DomainConfig": {
        "ElasticsearchClusterConfig": {
            "Status": {
                "PendingDeletion": false,
                "State": "Active",
                "CreationDate": 1543607549.411,
                "UpdateVersion": 5,
                "UpdateDate": 1543607985.146
            },
            "Options": {
                "DedicatedMasterEnabled": false,
                "InstanceCount": 1,
                "ZoneAwarenessEnabled": false,
                "InstanceType": "m4.large.elasticsearch"
            }
        },
        "VPCOptions": {
            "Status": {
                "PendingDeletion": false,
                "State": "Active",
                "CreationDate": 1543753704.204,
                "UpdateVersion": 8,
                "UpdateDate": 1543753704.204
            },
            "Options": {}
        },
        "CognitoOptions": {
            "Status": {
                "PendingDeletion": false,
                "State": "Active",
                "CreationDate": 1543753704.204,
                "UpdateVersion": 8,
                "UpdateDate": 1543753704.204
            },
            "Options": {
                "Enabled": false
            }
        },
        "EBSOptions": {
            "Status": {
                "PendingDeletion": false,
                "State": "Active",
                "CreationDate": 1543607549.411,
                "UpdateVersion": 5,
                "UpdateDate": 1543607985.146
            },
            "Options": {
                "VolumeSize": 10,
                "VolumeType": "gp2",
                "EBSEnabled": true
            }
        },
        "SnapshotOptions": {
            "Status": {
                "PendingDeletion": false,
                "State": "Active",
                "CreationDate": 1543607549.411,
                "UpdateVersion": 5,
                "UpdateDate": 1543607985.146
            },
            "Options": {
                "AutomatedSnapshotStartHour": 0
            }
        },
        "ElasticsearchVersion": {
            "Status": {
                "PendingDeletion": false,
                "State": "Active",
                "CreationDate": 1543607549.411,
                "UpdateVersion": 5,
                "UpdateDate": 1543607985.146
            },
            "Options": "6.3"
        },
        "LogPublishingOptions": {
            "Status": {
                "PendingDeletion": false,
                "State": "Active",
                "CreationDate": 1543753704.205,
                "UpdateVersion": 8,
                "UpdateDate": 1543753704.205
            },
            "Options": {}
        },
        "AdvancedOptions": {
            "Status": {
                "PendingDeletion": false,
                "State": "Active",
                "CreationDate": 1543607549.411,
                "UpdateVersion": 5,
                "UpdateDate": 1543607985.146
            },
            "Options": {
                "rest.action.multi.allow_explicit_index": "true"
            }
        },
        "EncryptionAtRestOptions": {
            "Status": {
                "PendingDeletion": false,
                "State": "Active",
                "CreationDate": 1543607549.411,
                "UpdateVersion": 5,
                "UpdateDate": 1543607985.146
            },
            "Options": {
                "Enabled": false
            }
        },
        "AccessPolicies": {
            "Status": {
                "PendingDeletion": false,
                "State": "Active",
                "CreationDate": 1543607549.411,
                "UpdateVersion": 5,
                "UpdateDate": 1543607985.146
            },
            "Options": "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Effect\":\"Allow\",\"Principal\":{\"AWS\":\"*\"},\"Action\":\"es:*\",\"Resource\":\"arn:aws:es:us-central-1:111122221111:domain/s3-log-ingester-pub/*\",\"Condition\":{\"IpAddress\":{\"aws:SourceIp\":\"10.14.98.227\"}}}]}"
        }
    }
}
```

### Update the new configuration
```sh
aws es update-elasticsearch-domain-config \
        --domain-name s3-log-ingester-pub \
        --elasticsearch-cluster-config InstanceType=t2.small.elasticsearch,InstanceCount=1,DedicatedMasterEnabled=false,ZoneAwarenessEnabled=false
```
The output should look like this,
```json
{
    "DomainConfig": {
        "ElasticsearchClusterConfig": {
            "Status": {
                "PendingDeletion": false,
                "State": "Processing",
                "CreationDate": 1543607549.411,
                "UpdateVersion": 9,
                "UpdateDate": 1543755247.218
            },
            "Options": {
                "DedicatedMasterEnabled": false,
                "InstanceCount": 1,
                "ZoneAwarenessEnabled": false,
                "InstanceType": "t2.small.elasticsearch"
            }
        },
        "VPCOptions": {
            "Status": {
                "PendingDeletion": false,
                "State": "Active",
                "CreationDate": 1543755247.37,
                "UpdateVersion": 9,
                "UpdateDate": 1543755247.37
            },
            "Options": {}
        },
        "CognitoOptions": {
            "Status": {
                "PendingDeletion": false,
                "State": "Active",
                "CreationDate": 1543755247.37,
                "UpdateVersion": 9,
                "UpdateDate": 1543755247.37
            },
            "Options": {
                "Enabled": false
            }
        },
        "EBSOptions": {
            "Status": {
                "PendingDeletion": false,
                "State": "Active",
                "CreationDate": 1543607549.411,
                "UpdateVersion": 5,
                "UpdateDate": 1543607985.146
            },
            "Options": {
                "VolumeSize": 10,
                "VolumeType": "gp2",
                "EBSEnabled": true
            }
        },
        "SnapshotOptions": {
            "Status": {
                "PendingDeletion": false,
                "State": "Active",
                "CreationDate": 1543607549.411,
                "UpdateVersion": 5,
                "UpdateDate": 1543607985.146
            },
            "Options": {
                "AutomatedSnapshotStartHour": 0
            }
        },
        "ElasticsearchVersion": {
            "Status": {
                "PendingDeletion": false,
                "State": "Active",
                "CreationDate": 1543607549.411,
                "UpdateVersion": 5,
                "UpdateDate": 1543607985.146
            },
            "Options": "6.3"
        },
        "LogPublishingOptions": {
            "Status": {
                "PendingDeletion": false,
                "State": "Active",
                "CreationDate": 1543755247.371,
                "UpdateVersion": 9,
                "UpdateDate": 1543755247.371
            },
            "Options": {}
        },
        "AdvancedOptions": {
            "Status": {
                "PendingDeletion": false,
                "State": "Active",
                "CreationDate": 1543607549.411,
                "UpdateVersion": 5,
                "UpdateDate": 1543607985.146
            },
            "Options": {
                "rest.action.multi.allow_explicit_index": "true"
            }
        },
        "EncryptionAtRestOptions": {
            "Status": {
                "PendingDeletion": false,
                "State": "Active",
                "CreationDate": 1543607549.411,
                "UpdateVersion": 5,
                "UpdateDate": 1543607985.146
            },
            "Options": {
                "Enabled": false
            }
        },
        "AccessPolicies": {
            "Status": {
                "PendingDeletion": false,
                "State": "Active",
                "CreationDate": 1543607549.411,
                "UpdateVersion": 5,
                "UpdateDate": 1543607985.146
            },
            "Options": "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Effect\":\"Allow\",\"Principal\":{\"AWS\":\"*\"},\"Action\":\"es:*\",\"Resource\":\"arn:aws:es:eu-central-1:111122221111:domain/s3-log-ingester-pub/*\",\"Condition\":{\"IpAddress\":{\"aws:SourceIp\":\"10.14.98.227\"}}}]}"
        }
    }
}
```
