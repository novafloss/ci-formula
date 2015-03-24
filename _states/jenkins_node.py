# -*- coding: utf-8 -*-
import difflib

import xml.etree.ElementTree as ET

import salt.exceptions as exc


_create_xml_template = """\
<?xml version="1.0" encoding="UTF-8"?>
<slave>
  <name>{node_name}</name>
  <description></description>
  <remoteFS>{node_slave_home}</remoteFS>
  <numExecutors>{executors}</numExecutors>
  <mode>NORMAL</mode>
  <retentionStrategy class="hudson.slaves.RetentionStrategy$Always"/>
  <launcher class="hudson.plugins.sshslaves.SSHLauncher" plugin="ssh-slaves@1.9">
    <host>{host}</host>
    <port>{ssh_port}</port>
    <credentialsId>{cred_id}</credentialsId>
    <launchTimeoutSeconds>10</launchTimeoutSeconds>
    <maxNumRetries>0</maxNumRetries>
    <retryWaitTime>5</retryWaitTime>
  </launcher>
  <label>{labels}</label>
  <nodeProperties/>
  <userId>{user_id}</userId>
</slave>"""  # noqa


def present(name, credential, host=None, remote_fs='', ssh_port=22,
            num_executors=None):
    _runcli = __salt__['jenkins.runcli']  # noqa
    ncpus = __grains__['num_cpus']  # noqa

    ret = {
        'name': name,
        'changes': {},
        'result': False,
        'comment': ''
    }

    new = _create_xml_template.format(
        node_name=name,
        host=host or name,
        node_slave_home=remote_fs,
        executors=num_executors or ncpus + 1,
        ssh_port=ssh_port,
        cred_id=credential,
        user_id='anonymous',
        labels='')

    try:
        current = _runcli('get-node', name)
    except Exception:
        current = ''
        command = 'create-node'
    else:
        command = 'update-node'

    if new == current:
        ret['result'] = True
        ret['comment'] = 'Node not changed.'
        return ret

    if not __opts__['test']:  # noqa
        try:
            ret['comment'] = _runcli(command, name, input_=new)
        except Exception, e:
            ret['comment'] = e.message
            return ret
        else:
            ret['result'] = True
    else:
        ret['result'] = None

    diff = '\n'.join(difflib.unified_diff(
        current.splitlines(), new.splitlines()))

    ret['comment'] = 'Changed'
    ret['changes'][name] = {
        'diff': diff,
    }
    return ret


def absent(name):
    _runcli = __salt__['jenkins.runcli']  # noqa

    ret = {
        'name': name,
        'changes': {},
        'result': False,
        'comment': ''
    }

    try:
        _runcli('get-node', name)
    except Exception:
        ret['comment'] = 'Already removed'
        ret['result'] = True
        return ret

    if not __opts__['test']:  # noqa
        try:
            ret['comment'] = _runcli('delete-node', name)
        except Exception, e:
            ret['comment'] = e.message
            return ret
        else:
            ret['result'] = True
    else:
        ret['result'] = None

    ret['changes'][name] = {
        'old': 'present',
        'new': 'absent',
    }
    return ret


def label_present(name, node):
    """Ensure jenkins label is present in a given node.

    name
        The name of the label to be present.

    view
        The target node.
    """

    _runcli = __salt__['jenkins.runcli']  # noqa
    test = __opts__['test']  # noqa

    ret = {
        'name': name,
        'changes': {},
        'result': False,
        'comment': ''
    }

    # check exist
    try:
        old = _runcli('get-node', node)
    except exc.CommandExecutionError as e:
        ret['comment'] = e.message
        return ret

    # parse node xml
    node_xml = ET.fromstring(old)

    # get merge with previous labels
    labels = [name] + (node_xml.find('label').text or '').split(' ')

    # parse, clean and update xml
    node_xml.find('label').text = ' '.join(sorted(set(labels)))

    # serialize new payload
    new = ET.tostring(node_xml.find('.'))

    # update if not testing
    if not test:
        try:
            _runcli('update-node', node, input_=new)
        except exc.CommandExecutionError as e:
            ret['comment'] = e.message
            return ret

    ret['changes'] = {
        'old': old,
        'new': new,
    }

    ret['result'] = None if test else True
    return ret


def label_absent(name, node):
    """Ensure jenkins label is absent in a given node.

    name
        The name of the label to be absent.

    view
        The target node.
    """

    _runcli = __salt__['jenkins.runcli']  # noqa
    test = __opts__['test']  # noqa

    ret = {
        'name': name,
        'changes': {},
        'result': False,
        'comment': ''
    }

    # check exist
    try:
        old = _runcli('get-node', node)
    except exc.CommandExecutionError as e:
        ret['comment'] = e.message
        return ret

    # parse node xml
    node_xml = ET.fromstring(old)

    # get previous labels except the one that should be absent
    labels = [l for l in (node_xml.find('label').text or '').split(' ')
              if l != name]

    # parse, clean and update xml
    node_xml.find('label').text = ' '.join(sorted(set(labels)))

    # serialize new payload
    new = ET.tostring(node_xml.find('.'))

    # update if not testing
    if not test:
        try:
            _runcli('update-node', node, input_=new)
        except exc.CommandExecutionError as e:
            ret['comment'] = e.message
            return ret

    ret['changes'] = {
        'old': old,
        'new': new,
    }

    ret['result'] = None if test else True
    return ret
