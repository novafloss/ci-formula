# -*- coding: utf-8 -*-
import xml.etree.ElementTree as ET

import salt.exceptions as exc


view_xml_tmpl = """
<hudson.model.ListView>
  <name>{name}</name>
  <filterExecutors>false</filterExecutors>
  <filterQueue>false</filterQueue>
  <properties class="hudson.model.View$PropertyList" />
  <jobNames>
    <comparator class="hudson.util.CaseInsensitiveComparator" />
  </jobNames>
  <jobFilters />
  <columns>
  </columns>
  <recurse>false</recurse>
</hudson.model.ListView>
"""  # noqa


def present(name, columns=None):
    """Ensures jenkins view is present.

    name
        The name of the view to be present.

    columns
        List of columns to add in the view.
    """

    _runcli = __salt__['jenkins.runcli']  # noqa
    test = __opts__['test']  # noqa

    ret = {
        'name': name,
        'changes': {},
        'result': None if test else True,
        'comment': ''
    }

    # check exist and continue or create
    try:
        _runcli('get-view', name)
        ret['comment'] = 'View `{0}` exists.'.format(name)
        return ret
    except exc.CommandExecutionError as e:
        pass

    # set columns
    view_xml = ET.fromstring(view_xml_tmpl.format(**{'name': name}))
    for c in columns or []:
        view_xml.find('columns').append(ET.Element(c))

    new = ET.tostring(view_xml.find('.'))

    # create
    if not test:
        try:
            _runcli('create-view', name, input_=new)
        except exc.CommandExecutionError as e:
            ret['comment'] = e.message
            ret['result'] = False
            return ret

    ret['changes'] = {
        'old': None,
        'new': new,
    }
    return ret


def absent(name):
    """Ensures jenkins view is absent.

    name
        The name of the view to be present.
    """

    _runcli = __salt__['jenkins.runcli']  # noqa
    test = __opts__['test']  # noqa

    ret = {
        'name': name,
        'changes': {},
        'result': None if test else True,
        'comment': ''
    }

    # check exist
    try:
        old = _runcli('get-view', name)
    except exc.CommandExecutionError as e:
        ret['comment'] = 'View `{0}` not found'.format(name)
        return ret

    # delete
    if not test:
        try:
            _runcli('delete-view', name)
        except exc.CommandExecutionError as e:
            ret['comment'] = e.message
            ret['result'] = False
            return ret

    ret['changes'] = {
        'old': old,
        'new': None,
    }

    return ret


def get_view_jobs(view_str):
    return [e.text for e in ET.fromstring(view_str).find('jobNames').findall('string')]  # noqa


def job_present(name, view):
    """Ensure jenkins job is present in a given view.

    name
        The name of the job to be present.

    view
        The target view.
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
        old = _runcli('get-view', view)
    except exc.CommandExecutionError as e:
        ret['comment'] = e.message
        return ret

    jobs = [name] + get_view_jobs(old)

    # parse, clean and update xml
    view_xml = ET.fromstring(old)
    view_xml.find('jobNames').clear()
    for job in sorted(set(jobs)):
        job_xml = ET.Element('string')
        job_xml.text = job
        view_xml.find('jobNames').append(job_xml)

    new = ET.tostring(view_xml.find('.'))

    # update if not testing
    if not test:
        try:
            _runcli('update-view', view, input_=new)
        except exc.CommandExecutionError as e:
            ret['comment'] = e.message
            return ret

    ret['changes'][view] = {
        'old': old,
        'new': new,
    }

    ret['result'] = None if test else True
    return ret