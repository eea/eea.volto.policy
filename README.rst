==========================
eea.volto.policy
==========================
.. image:: https://ci.eionet.europa.eu/buildStatus/icon?job=eea/eea.volto.policy/develop
  :target: https://ci.eionet.europa.eu/job/eea/job/eea.volto.policy/job/develop/display/redirect
  :alt: Develop
.. image:: https://ci.eionet.europa.eu/buildStatus/icon?job=eea/eea.volto.policy/master
  :target: https://ci.eionet.europa.eu/job/eea/job/eea.volto.policy/job/master/display/redirect
  :alt: Master

eea.volto.policy is the EEA Volto policy package for Plone.
The eea.volto.policy is a Plone add-on

It keeps stock Plone in place and layers EEA-specific REST API, navigation,
imaging, moderation, and admin behavior on top of it for Volto sites.

Check the `README.md <https://github.com/eea/eea.volto.policy/blob/master/eea/volto/policy/README.md>`_
for more details on the features and changes of this package.



.. contents::


Main features
=============

1. Easy to install/uninstall via Site Setup > Add-ons
2. GET @layout-blocks-duplicates - scans IBlocks content via the catalog, returns each affected item with UID, URL, and per-UUID occurrence locations. Supports path, portal_type, and b_size filters.
3. POST @layout-blocks-duplicates - repairs the reported items: deep-copies each duplicate block, assigns a fresh UUID, regenerates every UUID in the copied subtree, and patches blocks_layout.items in lockstep. Supports dry_run=1 for preview. Idempotent - a no-op on clean content.

Install
=======

* Add eea.volto.policy to your eggs section in your buildout and
  re-run buildout::

    [buildout]
    eggs +=
      eea.volto.policy

* You can download a sample buildout from:

  - https://github.com/eea/eea.volto.policy/tree/master/buildouts/plone4
  - https://github.com/eea/eea.volto.policy/tree/master/buildouts/plone5

* Or via docker::

    $ docker run --rm -p 8080:8080 -e ADDONS="eea.volto.policy" plone

* Install *eea.volto.policy* within Site Setup > Add-ons


Buildout installation
=====================

- `Plone 5+ <https://github.com/eea/eea.volto.policy/tree/master/buildouts/plone5>`_


Source code
===========

- `Plone 5+ on github <https://github.com/eea/eea.volto.policy>`_


Eggs repository
===============

- https://pypi.python.org/pypi/eea.volto.policy
- http://eggrepo.eea.europa.eu/simple


Plone versions
==============
It has been developed and tested for Plone 5 and 6. See buildout section above.


How to contribute
=================
See the `contribution guidelines (CONTRIBUTING.md) <https://github.com/eea/eea.volto.policy/blob/master/CONTRIBUTING.md>`_.

Copyright and license
=====================

eea.volto.policy (the Original Code) is free software; you can
redistribute it and/or modify it under the terms of the
GNU General Public License as published by the Free Software Foundation;
either version 2 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
for more details.

You should have received a copy of the GNU General Public License along
with this program; if not, write to the Free Software Foundation, Inc., 59
Temple Place, Suite 330, Boston, MA 02111-1307 USA.

The Initial Owner of the Original Code is European Environment Agency (EEA).
Portions created by Eau de Web are Copyright (C) 2009 by
European Environment Agency. All Rights Reserved.


Funding
=======

EEA_ - European Environment Agency (EU)

.. _EEA: https://www.eea.europa.eu/
.. _`EEA Web Systems Training`: http://www.youtube.com/user/eeacms/videos?view=1

Secret Scanning
===============

This repository uses the Betterleaks GitHub Action to scan the current
repository content on every push and pull request. The scan uses the rules in
``.gitleaks.toml`` and uploads a ``betterleaks-report`` artifact when a finding
is detected.

If the optional SMTP secrets are configured, failed scans also send an email to
the last commit committer. The workflow expects these repository or
organization secrets:

- ``SMTP_URL``
- ``SMTP_PORT`` (optional, defaults to ``25``)
- ``SMTP_EMAIL``
- ``SMTP_PASSWORD`` (optional if the SMTP server does not require authentication)

Port ``465`` is sent with direct TLS; other ports use the default SMTP
handshake. The email includes a short finding summary from the redacted
Betterleaks report, including the redacted matched line from each finding.

There are three common outcomes:

1. Everything is OK. The ``Betterleaks / Scan for secrets`` check is green and
   no action is needed. Regular references to runtime values are OK, for example::

     token_from_cookie = request.cookies.get("auth_token")

2. A real secret was found. The check is red and the workflow log asks you to
   download the ``betterleaks-report`` artifact. Open the artifact from the
   GitHub Actions run and check the reported file, line and rule. Remove the
   committed value, move it to the proper secret store, and rotate it if it was
   exposed. A report entry looks like this::

     {
       "RuleID": "secret-literal-assignment",
       "File": "src/config.py",
       "StartLine": 12,
       "Secret": "[REDACTED]"
     }

3. The finding is a false positive. Keep the value only if it is clearly not
   sensitive, such as a test fixture, placeholder, or public example. Add
   ``betterleaks:allow`` on the same line and include a short explanation in the
   pull request::

     test_password = "admin"  #betterleaks:allow

Do not add ``betterleaks:allow`` to real credentials.
