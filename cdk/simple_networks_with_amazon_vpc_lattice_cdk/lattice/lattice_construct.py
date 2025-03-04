from aws_cdk import Stack, aws_vpclattice
from constructs import Construct


# pylint: disable=too-many-instance-attributes
class LatticeConstruct(Construct):

    def __init__(self, scope: Construct, id_: str) -> None:
        super().__init__(scope, id_)
        self.id_ = id_
        self.scope = scope

        self.stack = Stack.of(self)
        self.region = self.stack.region
        self.account_id = self.stack.account

        self.service_network = self._build_service_network()

        self._associate_lattice_network_with_ec2_vpc()
        self._associate_lattice_network_with_ecs_vpc()
        self._associate_lattice_network_with_lambda_vpc()

        self.service_for_ec2 = self._build_service_for_ec2()
        self.service_for_lambda_function = self._build_service_for_lambda_function()
        self.service_for_ecs_cluster = self._build_service_ecs_cluster()

        self._associate_ec2_service_with_lattice_network()
        self._associate_ecs_service_with_lattice_network()
        self._associate_lambda_service_with_lattice_network()

        self.target_group_for_ec2 = self._build_target_group_for_ec2()
        self.target_group_for_ecs = self._build_target_group_for_ecs()
        self.target_group_for_lambda = self._build_target_group_for_lambda()

        self.listener_for_ec2 = self._build_listener_for_ec2()
        self.listener_for_ecs = self._build_listener_for_ecs()
        self.listener_for_lambda = self._build_listener_for_lambda()

        self._add_auth_policy_for_lambda()

    def _build_service_network(self) -> aws_vpclattice.CfnServiceNetwork:
        return aws_vpclattice.CfnServiceNetwork(
            self,
            "LatticeNetwork",
            name="latticenetwork",
        )

    def _associate_lattice_network_with_ec2_vpc(self) -> None:
        aws_vpclattice.CfnServiceNetworkVpcAssociation(self, "ec2vpcassociation", service_network_identifier=self.service_network.attr_arn,
                                                       vpc_identifier=self.scope.ec2_instance.ec2_vpc.vpc_id)

    def _associate_lattice_network_with_ecs_vpc(self) -> None:
        aws_vpclattice.CfnServiceNetworkVpcAssociation(self, "ecsvpcassociation", service_network_identifier=self.service_network.attr_arn,
                                                       vpc_identifier=self.scope.ecs_cluster.ecs_vpc.vpc_id)

    def _associate_lattice_network_with_lambda_vpc(self) -> None:
        aws_vpclattice.CfnServiceNetworkVpcAssociation(self, "lambdavpcassociation",
                                                       service_network_identifier=self.service_network.attr_arn,
                                                       vpc_identifier=self.scope.lambda_function.lambda_vpc.vpc_id)

    def _build_service_for_ec2(self) -> aws_vpclattice.CfnService:
        return aws_vpclattice.CfnService(self, "ec2service")

    def _build_service_for_lambda_function(self) -> aws_vpclattice.CfnService:
        return aws_vpclattice.CfnService(self, "lambdaservice", auth_type='AWS_IAM')

    def _build_service_ecs_cluster(self) -> aws_vpclattice.CfnService:
        return aws_vpclattice.CfnService(self, "ecsservice")

    def _associate_ec2_service_with_lattice_network(self) -> None:
        aws_vpclattice.CfnServiceNetworkServiceAssociation(self, "ec2serviceenetworkassociation",
                                                           service_identifier=self.service_for_ec2.attr_arn,
                                                           service_network_identifier=self.service_network.attr_arn)

    def _associate_lambda_service_with_lattice_network(self) -> None:
        aws_vpclattice.CfnServiceNetworkServiceAssociation(self, "lambdaserviceenetworkassociation",
                                                           service_identifier=self.service_for_lambda_function.attr_arn,
                                                           service_network_identifier=self.service_network.attr_arn)

    def _associate_ecs_service_with_lattice_network(self) -> None:
        aws_vpclattice.CfnServiceNetworkServiceAssociation(self, "ecsserviceenetworkassociation",
                                                           service_identifier=self.service_for_ecs_cluster.attr_arn,
                                                           service_network_identifier=self.service_network.attr_arn)

    def _build_target_group_for_ec2(self) -> aws_vpclattice.CfnTargetGroup:
        return aws_vpclattice.CfnTargetGroup(
            self, "ec2targetgroup", type="INSTANCE", name="ec2targetgroup", config=aws_vpclattice.CfnTargetGroup.TargetGroupConfigProperty(
                port=80,
                protocol="HTTP",
                vpc_identifier=self.scope.ec2_instance.ec2_vpc.vpc_id,
            ), targets=[aws_vpclattice.CfnTargetGroup.TargetProperty(id=self.scope.ec2_instance.ec2_instance.instance_id, port=80)])

    def _build_target_group_for_ecs(self) -> aws_vpclattice.CfnTargetGroup:
        return aws_vpclattice.CfnTargetGroup(
            self, "ecstargetgroup", type="ALB", name="ecstargetgroup", config=aws_vpclattice.CfnTargetGroup.TargetGroupConfigProperty(
                port=80,
                protocol="HTTP",
                vpc_identifier=self.scope.ecs_cluster.ecs_vpc.vpc_id,
            ), targets=[aws_vpclattice.CfnTargetGroup.TargetProperty(id=self.scope.ecs_cluster.alb.load_balancer_arn, port=80)])

    def _build_target_group_for_lambda(self) -> aws_vpclattice.CfnTargetGroup:
        return aws_vpclattice.CfnTargetGroup(
            self, "lambdatargetgroup", type="LAMBDA", name="lambdatargetgroup",
            targets=[aws_vpclattice.CfnTargetGroup.TargetProperty(id=self.scope.lambda_function.lambda_function.function_arn)])

    def _build_listener_for_ec2(self) -> aws_vpclattice.CfnListener:
        return aws_vpclattice.CfnListener(
            self,
            "ec2listener",
            default_action=aws_vpclattice.CfnListener.DefaultActionProperty(
                forward=aws_vpclattice.CfnListener.ForwardProperty(target_groups=[
                    aws_vpclattice.CfnListener.WeightedTargetGroupProperty(target_group_identifier=self.target_group_for_ec2.attr_arn,
                                                                           weight=100)
                ])),
            protocol="HTTP",
            port=80,
            service_identifier=self.service_for_ec2.attr_arn,
        )

    def _build_listener_for_ecs(self) -> aws_vpclattice.CfnListener:
        return aws_vpclattice.CfnListener(
            self,
            "ecslistener",
            default_action=aws_vpclattice.CfnListener.DefaultActionProperty(
                forward=aws_vpclattice.CfnListener.ForwardProperty(target_groups=[
                    aws_vpclattice.CfnListener.WeightedTargetGroupProperty(target_group_identifier=self.target_group_for_ecs.attr_arn,
                                                                           weight=100)
                ])),
            protocol="HTTP",
            port=80,
            service_identifier=self.service_for_ecs_cluster.attr_arn,
        )

    def _build_listener_for_lambda(self) -> aws_vpclattice.CfnListener:
        return aws_vpclattice.CfnListener(
            self,
            "lambdalistener",
            default_action=aws_vpclattice.CfnListener.DefaultActionProperty(
                forward=aws_vpclattice.CfnListener.ForwardProperty(target_groups=[
                    aws_vpclattice.CfnListener.WeightedTargetGroupProperty(target_group_identifier=self.target_group_for_lambda.attr_arn,
                                                                           weight=100)
                ])),
            protocol="HTTP",
            port=80,
            service_identifier=self.service_for_lambda_function.attr_arn,
        )

    def _add_auth_policy_for_lambda(self) -> None:
        # Allow calls to this Lambda only from the EC2
        aws_vpclattice.CfnAuthPolicy(
            self, "lambdaserviceauthpolicy", policy={
                "Version":
                    "2012-10-17",
                "Statement": [{
                    "Effect": "Allow",
                    "Principal": "*",
                    "Action": "vpc-lattice-svcs:Invoke",
                    "Resource": "*",
                    "Condition": {
                        "StringEquals": {
                            "vpc-lattice-svcs:SourceVpc": f'{self.scope.ec2_instance.ec2_vpc.vpc_id}'
                        }
                    }
                }]
            }, resource_identifier=self.service_for_lambda_function.attr_arn)
