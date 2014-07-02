import unittest
import mock
from datetime import datetime
import json
from .messages import HipchatMessage


def setup_mock_request(mock_method, status_code, json_data):
    mock_response = mock.Mock()
    mock_response.read.return_value = json.dumps(json_data)
    mock_response.getcode.return_value = status_code
    mock_method.return_value = mock_response


def mock_hipchat_ok_request(mock_method):
    data = {'status': 'sent'}
    return setup_mock_request(mock_method, 200, data)


def mock_hipchat_error_request(mock_method):
    data = {'error': {'message': 'some test error', 'type': 'Unauthorized', 'code': 401}}
    return setup_mock_request(mock_method, 401, data)


class MessageTest(unittest.TestCase):
    def setUp(self):
        #"$HOSTNAME$|$LONGDATETIME$|$NOTIFICATIONTYPE$|$HOSTADDRESS$|$HOSTSTATE$|$HOSTOUTPUT$|$NOTES$|$NOTESURL$"
        self.host_inputs = 'hostname|%(longdatetime)s|%(notificationtype)s|127.0.0.1|' \
                        '%(hoststate)s|NAGIOS_OUTPUT|This is a test note|http://myurl.com/testhostnote'
        #"$SERVICEDESC$|$HOSTALIAS$|$LONGDATETIME$|$NOTIFICATIONTYPE$|$HOSTADDRESS$|$SERVICESTATE$
        # |$SERVICEOUTPUT$|$NOTES$|$NOTESURL$"
        self.service_inputs = 'servicedesc|hostalias|%(longdatetime)s|%(notificationtype)s|' \
                        '127.0.0.1|%(servicestate)s|NAGIOS_OUTPUT|This is a test service note|http://myurl.com/testservicenote'

    @mock.patch('hipsaint.messages.urlopen')
    def test_ok_payload_delivery(self, mock_get):
        mock_hipchat_ok_request(mock_get)
        msg_inputs = self.host_inputs % {'longdatetime': datetime.now(),
                                         'notificationtype': 'PROBLEM',
                                         'hoststate': 'DOWN'}
        problem_msg = HipchatMessage('host', msg_inputs, None, None, None, False)
        response = problem_msg.deliver_payload()
        self.assertEqual(response.getcode(), 200)
        response_data = json.load(response)
        self.assertEqual(response_data['status'], 'sent')

    @mock.patch('hipsaint.messages.urlopen')
    def test_error_payload_delivery(self, mock_get):
        mock_hipchat_error_request(mock_get)
        msg_inputs = self.host_inputs % {'longdatetime': datetime.now(),
                                         'notificationtype': 'PROBLEM',
                                         'hoststate': 'DOWN', 'notes': 'This is a test note',
                                         'notesurl': 'http://myurl.com/testhostnote'}
        problem_msg = HipchatMessage('host', msg_inputs, None, None, None, False)
        response = problem_msg.deliver_payload()
        response_data = json.load(response)
        self.assertEqual(response.getcode(), 401)
        self.assertTrue('error' in response_data)

    def test_render_host(self):
        message_type = 'host'
        msg_inputs = self.host_inputs % {'longdatetime': datetime.now(),
                                         'notificationtype': 'PROBLEM',
                                         'hoststate': 'DOWN'}
        problem_msg = HipchatMessage(message_type, msg_inputs, None, None, None, False)
        problem_msg.render_message()
        self.assertEqual(problem_msg.message_color, 'red')

        # Test short host
        problem_msg = HipchatMessage('short-host', msg_inputs, None, None, None, False)
        problem_msg.render_message()
        self.assertEqual(problem_msg.message_color, 'red')

        msg_inputs = self.host_inputs % {'longdatetime': datetime.now(),
                                         'notificationtype': 'RECOVERY',
                                         'hoststate': 'UP'}
        problem_msg = HipchatMessage(message_type, msg_inputs, None, None, None, False)
        problem_msg.render_message()
        self.assertEqual(problem_msg.message_color, 'green')

        msg_inputs = self.host_inputs % {'longdatetime': datetime.now(),
                                         'notificationtype': 'UNREACHABLE',
                                         'hoststate': 'UKNOWN'}
        problem_msg = HipchatMessage(message_type, msg_inputs, None, None, None, False)
        problem_msg.render_message()
        self.assertEqual(problem_msg.message_color, 'red')

        msg_inputs = self.host_inputs % {'longdatetime': datetime.now(),
                                         'notificationtype': 'ACKNOWLEDGEMENT',
                                         'hoststate': 'DOWN'}
        problem_msg = HipchatMessage(message_type, msg_inputs, None, None, None, False)
        problem_msg.render_message()
        self.assertEqual(problem_msg.message_color, 'purple')

    def test_render_service(self):
        message_type = 'service'
        msg_inputs = self.service_inputs % {'longdatetime': datetime.now(),
                                            'notificationtype': 'PROBLEM',
                                            'servicestate': 'WARNING'}
        problem_msg = HipchatMessage(message_type, msg_inputs, None, None, None, False)
        problem_msg.render_message()
        self.assertEqual(problem_msg.message_color, 'yellow')

        msg_inputs = self.service_inputs % {'longdatetime': datetime.now(),
                                            'notificationtype': 'PROBLEM',
                                            'servicestate': 'CRITICAL'}
        problem_msg = HipchatMessage(message_type, msg_inputs, None, None, None, False)
        problem_msg.render_message()
        self.assertEqual(problem_msg.message_color, 'red')

        # Test short service
        problem_msg = HipchatMessage('short-service', msg_inputs, None, None, None, False)
        problem_msg.render_message()
        self.assertEqual(problem_msg.message_color, 'red')

        msg_inputs = self.service_inputs % {'longdatetime': datetime.now(),
                                            'notificationtype': 'PROBLEM',
                                            'servicestate': 'UNKNOWN'}
        problem_msg = HipchatMessage(message_type, msg_inputs, None, None, None, False)
        problem_msg.render_message()
        self.assertEqual(problem_msg.message_color, 'gray')

        msg_inputs = self.service_inputs % {'longdatetime': datetime.now(),
                                            'notificationtype': 'RECOVERY',
                                            'servicestate': 'OK'}
        problem_msg = HipchatMessage(message_type, msg_inputs, None, None, None, False)
        problem_msg.render_message()
        self.assertEqual(problem_msg.message_color, 'green')

        msg_inputs = self.service_inputs % {'longdatetime': datetime.now(),
                                            'notificationtype': 'ACKNOWLEDGEMENT',
                                            'servicestate': 'CRITICAL'}
        problem_msg = HipchatMessage(message_type, msg_inputs, None, None, None, False)
        problem_msg.render_message()
        self.assertEqual(problem_msg.message_color, 'purple')
