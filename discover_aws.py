import boto3
from pprint import pprint

# Config ~/.aws/config
# [default]
# aws_access_key_id = ...
# aws_secret_access_key = ...


region = 'us-east-1'

class DiscoverEC2(object):

    def __init__(self, region):
        self.region = region
        self.list_inventory = list()
        self.ec2 = boto3.resource('ec2', self.region)


    def extract_data(self):
        for instance in self.ec2.instances.all():
            self.current_instance = instance

            meta_data = instance.meta.data
            data = {
                'server_name': self.get_server_name(meta_data),
                'system_type': 'Virtual Machine - AWS',
                'tags': meta_data.get('Tags'),
                'provider': 'AWS',
                'instance_type': meta_data.get('InstanceType'),
                'region': self.region,
                'operating_system': self.get_operating_system(instance),
                'count_cpu': meta_data['CpuOptions']['CoreCount'],
                'total_storage': self.get_total_storage(instance)
            }

            self.list_inventory.append(data)


    def get_server_name(self, data):
        for tag in data.get('Tags'):
            if tag['Key'] == 'Name':
                return tag['Value']
        return 'Undefined'

    def get_operating_system(self, instance):
        platform = getattr(instance.image, 'platform', 'Undefined')
        if not platform:
            platform = 'Undefined'

        return platform

    def get_total_storage(self, instance):
        # Expresado en Gb.
        return sum([volume.size for volume in instance.volumes.all()])


if __name__ == '__main__':
    ec2 = DiscoverEC2(region)
    ec2.extract_data()

    for vm in ec2.list_inventory:
        pprint(vm, indent=3)
        print('\n')

