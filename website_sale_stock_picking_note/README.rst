===============================
Website Sale Stock Picking Note
===============================

.. !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
   !! This file is generated by oca-gen-addon-readme !!
   !! changes will be overwritten.                   !!
   !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

.. |badge1| image:: https://img.shields.io/badge/maturity-Beta-yellow.png
    :target: https://odoo-community.org/page/development-status
    :alt: Beta
.. |badge2| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3
.. |badge3| image:: https://img.shields.io/badge/github-OCA%2Fe--commerce-lightgray.png?logo=github
    :target: https://github.com/OCA/e-commerce/tree/12.0/website_sale_stock_picking_note
    :alt: OCA/e-commerce
.. |badge4| image:: https://img.shields.io/badge/weblate-Translate%20me-F47D42.png
    :target: https://translation.odoo-community.org/projects/e-commerce-12-0/e-commerce-12-0-website_sale_stock_picking_note
    :alt: Translate me on Weblate
.. |badge5| image:: https://img.shields.io/badge/runbot-Try%20me-875A7B.png
    :target: https://runbot.odoo-community.org/runbot/113/12.0
    :alt: Try me on Runbot

|badge1| |badge2| |badge3| |badge4| |badge5| 

This module allows the clients to set a comment on the orders from website.

With this module we want to allow internal users to fulfill website orders in behalf
of the customers. For this we can't use the extra step because the comment set there is
not connected to a real field.

**Table of contents**

.. contents::
   :local:

Configuration
=============

If you want to disable that module, you can go to *Settings > General Settings > Website*
and select the option 'Disable custom delivery comment feature'.

Usage
=====

When a client realice an order from website, he/she has the field 'Custom delivery comment'
on the payment page. There he/she can input the comment.

After confirm the order by the client:
    #. Go to *Website > Orders > Unpaid Orders* select the order that the client has
       done.
    #. Go to 'Other information' and you can see the comment on 'Picking Note' field.
    #. Confirm the order and go to the picking.
    #. Go to 'Note' and there you can see the comment on the picking.

Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/OCA/e-commerce/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and welcomed
`feedback <https://github.com/OCA/e-commerce/issues/new?body=module:%20website_sale_stock_picking_note%0Aversion:%2012.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.

Do not contact contributors directly about support or help with technical issues.

Credits
=======

Authors
~~~~~~~

* Tecnativa

Contributors
~~~~~~~~~~~~

* `Tecnativa <https://www.tecnativa.com>`_:

  * David Vidal
  * Carlos Roca

Maintainers
~~~~~~~~~~~

This module is maintained by the OCA.

.. image:: https://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: https://odoo-community.org

OCA, or the Odoo Community Association, is a nonprofit organization whose
mission is to support the collaborative development of Odoo features and
promote its widespread use.

.. |maintainer-CarlosRoca13| image:: https://github.com/CarlosRoca13.png?size=40px
    :target: https://github.com/CarlosRoca13
    :alt: CarlosRoca13

Current `maintainer <https://odoo-community.org/page/maintainer-role>`__:

|maintainer-CarlosRoca13| 

This module is part of the `OCA/e-commerce <https://github.com/OCA/e-commerce/tree/12.0/website_sale_stock_picking_note>`_ project on GitHub.

You are welcome to contribute. To learn how please visit https://odoo-community.org/page/Contribute.
