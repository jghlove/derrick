#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

import os

from jinja2 import Template

from derrick.core.command import Command
from derrick.core.common import *
from derrick.core.derrick import Derrick
from derrick.core.exceptions import RiggingCompileException, ParamsShortageException
from derrick.core.logger import Logger


class Init(Command):
    # implement the interface
    def execute(self, context):
        rigging_manager = Derrick().get_rigging_manager()
        all_rigging = rigging_manager.all()

        detected = False
        handled_rigging = []
        for rigging_name in all_rigging:
            rigging = all_rigging.get(rigging_name)
            try:
                handled, platform = rigging.detect(context)
                if handled == True:
                    detected = True
                    handled_rigging.append({"rigging_name": rigging_name, "rigging": rigging, "platform": platform})
            except Exception as e:
                Logger.debug("Failed to detect your application's platform with rigging(%s),because of %s"
                             % (rigging_name, e.message))
        if detected != False:
            if len(handled_rigging) > 1:
                # TODO when more than one rigging can handle your application.
                pass
            else:
                rigging_dict = handled_rigging[0]
                rigging = rigging_dict.get("rigging")
                try:
                    results = rigging.compile(context)
                    Logger.debug("The platform is %s,the rigging used is %s"
                                 % (rigging_dict.get("platform"), rigging_dict.get("rigging_name")))
                    Logger.debug("The results is %s" % results)
                except Exception as e:
                    Logger.error("Failed to compile your application.because of %s" % e.message)

                if type(results) is dict:
                    try:
                        template_dir = rigging.get_template_dir()
                        dest_dir = context.get(WORKSPACE)
                        self.render_templates(templates_dir=template_dir, dest_dir=dest_dir, compile_dict=results)
                    except Exception as e:
                        Logger.error("")
                else:
                    raise RiggingCompileException("compile results is not a dict")
        else:
            Logger.warn(
                "Failed to detect your application's platform."
                "Maybe you can upgrade Derrick to get more platforms supported.")

    def get_help_desc(self):
        return "derrick init (-d | --debug)"

    # TODO Maybe you can alse define your custom template render using ExtensionPoints
    # Render all templates to dest workspace
    def render_templates(self, templates_dir=None, dest_dir=None, compile_dict=None):
        if templates_dir == None or dest_dir == None or compile_dict == None:
            raise ParamsShortageException("compile templates need some more params")
        all_success = True
        for template_name in compile_dict.keys():
            template_path = os.path.join(templates_dir, template_name)
            try:
                self.render_template(template_path, dest_dir, compile_dict.get(template_name))
            except Exception as e:
                all_success = False
                Logger.warn("Failed to compile template(%s),because of %s" % (template_name, e.message))
        return all_success

    # Render single file to workspace
    def render_template(self, template_path, dest_dir, content):
        converted_content = None
        template_file = os.path.basename(template_path)

        with open(template_path) as f:
            template_content = f.read()
            # If template is jinjia template then render the template or just move the template
            if template_file.endswith(".j2"):
                dest_file_name = template_file[:-3]
                template = Template(template_content)
                converted_content = template.render(content)
            else:
                dest_file_name = template_file

        dest_file_path = os.path.join(dest_dir, dest_file_name)

        with open(dest_file_path, "w") as dest_file:
            dest_file.write(converted_content)