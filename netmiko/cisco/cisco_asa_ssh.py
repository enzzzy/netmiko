'''
Subclass specific to Cisco ASA
'''

from __future__ import unicode_literals
from netmiko.ssh_connection import SSHConnection
from netmiko.netmiko_globals import MAX_BUFFER
import time
import re

class CiscoAsaSSH(SSHConnection):
    '''
    Subclass specific to Cisco ASA
    '''

    def session_preparation(self):
        '''
        Prepare the session after the connection has been established

        ASA must go into enable mode to disable_paging
        '''

        self.enable()
        self.disable_paging(command="terminal pager 0\n")
        self.set_base_prompt()


    def send_command(self, command_string, delay_factor=.5, max_loops=30,
                     strip_prompt=True, strip_command=True):
        '''
        If the ASA is in multi-context mode, then the base_prompt needs to be
        updated after each context change.
        '''
        output = super(CiscoAsaSSH, self).send_command(command_string, delay_factor,
                                                       max_loops, strip_prompt, strip_command)
        if "changeto" in command_string:
            self.set_base_prompt()
        return output


    def set_base_prompt(self, *args, **kwargs):
        '''
        Cisco ASA in multi-context mode needs to have the base prompt updated
        (if you switch contexts i.e. 'changeto')

        This switch of ASA contexts can occur in configuration mode. If this
        happens the trailing '(config*' needs stripped off.
        '''
        cur_base_prompt = super(CiscoAsaSSH, self).set_base_prompt(*args, **kwargs)
        match = re.search(r'(.*)\(conf.*', cur_base_prompt)
        if match:
            # strip off (conf.* from base_prompt
            self.base_prompt = match.group(1)
            return self.base_prompt


    def enable(self):
        '''
        Enter enable mode

        Must manually control the channel at this point for ASA
        '''

        delay_factor = .5

        self.clear_buffer()
        self.remote_conn.send("\nenable\n")
        time.sleep(1*delay_factor)

        output = self.remote_conn.recv(MAX_BUFFER)
        if 'password' in output.lower():
            self.remote_conn.send(self.secret+'\n')
            self.remote_conn.send('\n')
            time.sleep(1*delay_factor)
            output += self.remote_conn.recv(MAX_BUFFER)

        self.set_base_prompt()
        self.clear_buffer()
