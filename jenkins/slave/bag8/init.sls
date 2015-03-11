{% set jenkins = pillar.get('jenkins', {}) -%}
{% set home = jenkins.get('home', '/usr/local/jenkins') -%}
{% set user = jenkins.get('user', 'jenkins') -%}

include:
  - bag8

bag8_config_dir:
  file.directory:
    - name: {{ home }}/.config
    - user: {{ user }}
    - makedirs: True

bag8_local_dir:
  file.directory:
    - name: {{ home }}/.local
    - user: {{ user }}
    - makedirs: True
