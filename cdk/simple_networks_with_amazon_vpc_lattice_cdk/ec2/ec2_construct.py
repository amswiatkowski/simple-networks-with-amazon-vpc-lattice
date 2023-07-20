from pathlib import Path

from aws_cdk import Stack, aws_ec2
from constructs import Construct

from cdk.simple_networks_with_amazon_vpc_lattice_cdk.constants import EC2_KEY_NAME


class EC2Construct(Construct):

    def __init__(self, scope: Construct, id_: str) -> None:
        super().__init__(scope, id_)
        self.id_ = id_
        self.scope = scope

        self.stack = Stack.of(self)
        self.region = self.stack.region
        self.account_id = self.stack.account

        self.ec2_vpc = self._build_ec2_vpc()
        self.ec2_security_group = self._build_ec2_security_group()
        self.ec2_instance = self._build_ec2_instance()

    def _build_ec2_vpc(self) -> aws_ec2.Vpc:
        return aws_ec2.Vpc(
            self, 'Ec2Vpc', ip_addresses=aws_ec2.IpAddresses.cidr('10.0.0.0/16'), max_azs=1, nat_gateways=0,
            subnet_configuration=[aws_ec2.SubnetConfiguration(name='Ec2PublicSubnet', subnet_type=aws_ec2.SubnetType.PUBLIC, cidr_mask=24)])

    def _build_ec2_security_group(self) -> aws_ec2.SecurityGroup:
        security_group = aws_ec2.SecurityGroup(
            self,
            'Ec2SG',
            vpc=self.ec2_vpc,
            allow_all_outbound=True,
        )
        security_group.add_ingress_rule(peer=aws_ec2.Peer.any_ipv4(), description='inbound SSH', connection=aws_ec2.Port.tcp(22))
        security_group.add_ingress_rule(peer=aws_ec2.Peer.any_ipv4(), description='inbound HTTP', connection=aws_ec2.Port.tcp(80))
        return security_group

    def _get_user_data_script(self) -> str:
        path = Path.cwd() / "cdk/simple_networks_with_amazon_vpc_lattice_cdk/ec2/user_data.sh"

        return path.read_text(encoding="utf-8")

    def _build_ec2_instance(self) -> aws_ec2.Instance:
        ec2_instance = aws_ec2.Instance(self, 'WebSrvEc2', instance_name='WebSrvEc2',
                                        instance_type=aws_ec2.InstanceType.of(aws_ec2.InstanceClass.T3, aws_ec2.InstanceSize.NANO),
                                        machine_image=aws_ec2.MachineImage.latest_amazon_linux2(), vpc=self.ec2_vpc,
                                        vpc_subnets=aws_ec2.SubnetSelection(subnet_type=aws_ec2.SubnetType.PUBLIC),
                                        security_group=self.ec2_security_group, key_name=EC2_KEY_NAME)
        ec2_instance.add_user_data(self._get_user_data_script())

        return ec2_instance
