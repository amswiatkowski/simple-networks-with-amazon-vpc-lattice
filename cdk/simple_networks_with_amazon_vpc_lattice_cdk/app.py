#!/usr/bin/env python3
import os

from aws_cdk import App, Environment
from boto3 import client, session
from simple_networks_with_amazon_vpc_lattice_cdk.simple_networks_with_amazon_vpc_lattice_stack import (
    SimpleNetworksWithAmazonVpcLatticeStack,
    get_stack_name,
)

account = client('sts').get_caller_identity()['Account']
region = session.Session().region_name
app = App()
simple_networks_with_amazon_vpc_lattice_stack = SimpleNetworksWithAmazonVpcLatticeStack(
    app,
    get_stack_name(),
    env=Environment(account=os.environ.get('AWS_DEFAULT_ACCOUNT', account), region=os.environ.get('AWS_DEFAULT_REGION', region)),
)
app.synth()
