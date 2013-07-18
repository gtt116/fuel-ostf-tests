from nose.plugins.attrib import attr
from nose.tools import timed

from fuel_health.common.ssh import Client as SSHClient
from fuel_health.exceptions import SSHExecCommandFailed
from fuel_health.tests.sanity import base


class SanityInfrastructureTest(base.BaseComputeAdminTest):
    """
    TestClass contains tests check the whole OpenStack availability.
    Special requirements:
            1. A controller's IP should be specified in
                controller_node parameter of the config file.
            2. The controller's domain name should be specified in
                controller_node_name parameter of the config file.
            3. SSH user credentials should be specified in
                controller_node_ssh_user/password parameters
                of the config file.
            4. List of services are expected to be run should be specified in
                enabled_services parameter of the config file.
    """
    _interface = 'json'

    @classmethod
    def setUpClass(cls):
        cls.list_of_expected_services = cls.config.compute.enabled_services
        cls.host = cls.config.compute.controller_nodes
        cls.usr = cls.config.compute.controller_node_ssh_user
        cls.pwd = cls.config.compute.controller_node_ssh_password
        cls.key = cls.config.compute.controller_node_ssh_key_path
        cls.hostname = cls.config.compute.controller_nodes_name
        cls.timeout = cls.config.compute.ssh_timeout

    @classmethod
    def tearDownClass(cls):
        pass

    @attr(type=['sanity', 'fuel'])
    @timed(5.5)
    def test_services_state(self):
        """Test all of the expected services are on.
        Target component: OpenStack

        Scenario:
            1. Connect to a controller node via SSH.
            2. Execute nova-manage service list command.
            3. Check there is no failed services (with XXX state)
                in the command output.
            4. Check number of normally executed services (with :-) state
                is equal to the number of expected services
        Duration: 1.5-5.6 s.
        """
        output_msg = ''
        cmd = 'nova-manage service list'
        if len(self.hostname) and len(self.host):

            try:
                output = SSHClient(self.host[0],
                                   self.usr, self.pwd,
                                   key_filename=self.key,
                                   timeout=self.timeout).exec_command(cmd)
            except SSHExecCommandFailed:
                output_msg = "Error: 'nova-manage' command execution failed."

            output_msg = output_msg or (
                'Some service has not been started:' + str(
                    self.list_of_expected_services))
            self.assertFalse(u'XXX' in output, output_msg)
            self.assertTrue(len(self.list_of_expected_services) <=
                            output.count(u':-)'),
                            output_msg)
        else:
            self.fail('Wrong tests configurations, one from the next '
                      'parameters are empty controller_node_name or '
                      'controller_node_ip ')

    @attr(type=['sanity', 'fuel'])
    @timed(5.5)
    def test_dns_state(self):
        """Test dns is available.
        Target component: OpenStack

        Scenario:
            1. Connect to a controller node via SSH.
            2. Execute host command for the controller IP.
            3. Check expected controller's domain name is present
                in the command output to be sure the domain name
                was successfully resolved.
        Duration: 1.2-5.6 s.
        """
        if len(self.hostname) and len(self.host):
            expected_output = "in-addr.arpa domain name pointer"
            cmd = "host " + self.host[0]
            try:
                output = SSHClient(self.host[0], self.usr, self.pwd,
                                   pkey=self.key, timeout=self.timeout).exec_command(cmd)
            except SSHExecCommandFailed:
                output = "'host' command failed."
            self.assertTrue(expected_output in output,
                            'DNS name cannot be resolved')
        else:
            self.fail('Wrong tests configurations, one from the next '
                      'parameters are empty controller_node_name or '
                      'controller_node_ip ')
