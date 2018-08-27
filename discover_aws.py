from pprint import pprint

import boto3
from botocore.exceptions import ClientError

import logging

# Config ~/.aws/config
# [default]
# aws_access_key_id = ...
# aws_secret_access_key = ...
logger = logging.getLogger(__name__)


region = 'us-east-1'

class DiscoverEC2(object):

    def __init__(self, region):
        self.region = region
        self.ec2 = boto3.resource('ec2', self.region)
        self.account_id = self.get_account_id()
        self.inventory = self.prepare_inventory()

    def prepare_inventory(self):
        inventory = {
            'region': self.region,
            'account_id': self.get_account_id(),
            'provider': 'AWS',
            'system_type': 'Virtual Machine - AWS',
            'instances': list()
        }
        return inventory


    def extract_data(self):
        for instance in self.ec2.instances.all():
            self.current_instance = instance

            meta_data = instance.meta.data
            data = {
                'server_name': self.get_server_name(meta_data),
                'tags': meta_data.get('Tags'),
                'instance_type': meta_data.get('InstanceType'),
                'platform': self.get_platform(instance),
                'count_cpu': meta_data['CpuOptions']['CoreCount'],
                'total_storage': self.get_total_storage(instance),

            }

            self.inventory['instances'].append(data)


    def get_server_name(self, data):
        for tag in data.get('Tags'):
            if tag['Key'] == 'Name':
                return tag['Value']
        return 'Undefined'

    def get_platform(self, instance):
        # The value is Windows for Windows AMIs; otherwise blank.
        platform = getattr(instance.image, 'platform', 'Linux')
        if not platform:
            platform = 'Linux'

        return platform

    def get_total_storage(self, instance):
        # Expresado en Gb.
        return sum([volume.size for volume in instance.volumes.all()])

    def get_account_id(self):
        # https://boto3.readthedocs.io/en/latest/reference/services/sts.html?highlight=sts
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        return identity['Account']

    # Pricing
    def get_pricing(self):
        # https://boto3.readthedocs.io/en/latest/reference/services/pricing.html
        try:
            pricing = boto3.client('pricing', self.region)
            describe_services = pricing.describe_services()
        except ClientError as client_error:
            logger.warning(client_error.message)
            describe_services = client_error.message

        return describe_services



if __name__ == '__main__':
    ec2 = DiscoverEC2(region)
    ec2.extract_data()

    print('Account ID: {}'.format(ec2.inventory['account_id']))
    print('Provider: {}'.format(ec2.inventory['provider']))
    print('System Type: {}'.format(ec2.inventory['system_type']))
    print('Region: {}'.format(ec2.inventory['region']))

    print('Instances')
    for vm in ec2.inventory['instances']:
        pprint(vm, indent=3)
        print('\n')

