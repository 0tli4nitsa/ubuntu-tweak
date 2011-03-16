# Ubuntu Tweak - Ubuntu Configuration Tool
#
# Copyright (C) 2007-2011 Tualatrix Chou <tualatrix@gmail.com>
#
# Ubuntu Tweak is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# Ubuntu Tweak is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ubuntu Tweak; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA

import os
import logging

import gobject
from gi.repository import Gtk, Unique, Pango, GdkPixbuf

from ubuntutweak import modules
from ubuntutweak.gui import GuiBuilder
from ubuntutweak.utils import icon
from ubuntutweak.common.consts import VERSION, DATA_DIR
from ubuntutweak.modules import ModuleLoader

log = logging.getLogger('app')

MODULE_LOADER = ModuleLoader(modules.__path__[0])


def show_splash():
    win = Gtk.Window(type=Gtk.WindowType.POPUP)
    win.set_position(Gtk.WindowPosition.CENTER)

    vbox = Gtk.VBox()
    image = Gtk.Image()
    image.set_from_file(os.path.join(DATA_DIR, 'pixmaps/splash.png'))

    vbox.pack_start(image, True, True, 0)
    win.add(vbox)

    win.show_all()

    while Gtk.events_pending():
        Gtk.main_iteration()

    win.destroy()


class WelcomePage(Gtk.VBox):
    def __init__(self):
        gobject.GObject.__init__(self)

        self.set_border_width(20)

        title = Gtk.MenuItem(label='')
        label = title.get_child()
        label.set_markup(_('\n<span size="xx-large">Welcome to <b>Ubuntu Tweak!</b></span>\n'))
        label.set_alignment(0.5, 0.5)
        title.select()
        self.pack_start(title, False, False, 10)

        tips = self.create_tips(
                _('Tweak otherwise hidden settings.'),
                _('Clean up unused packages to free up diskspace.'),
                _('Easily install up-to-date versions of many applications.'),
                _('Configure file templates and shortcut scripts for easy access to common tasks.'),
                _('Many more useful features!'),
                )

    def create_tips(self, *tips):
        for tip in tips:
            hbox = Gtk.HBox()
            image = Gtk.Image.new_from_stock(Gtk.STOCK_GO_FORWARD,
                                             Gtk.IconSize.BUTTON)
            hbox.pack_start(image, False, False, 15)

            label = Gtk.Label()
            label.set_alignment(0.0, 0.5)
            label.set_ellipsize(Pango.EllipsizeMode.END)
            label.set_markup(tip)
            hbox.pack_start(label, True, True, 0)

            self.pack_start(hbox, False, False, 10)


class ModuleTreeView(Gtk.TreeView):
    (NAME_COLUMN,
     LOGO_COLUMN,
     TITLE_COLUMN,
     MODULE_CLASS) = range(4)

    def __init__(self):
        gobject.GObject.__init__(self)

        self.set_headers_visible(False)
        self._add_columns()

        model = self._create_model()
        self.set_model(model)
        self.update_model()

        self.connect('realize', lambda tv: tv.expand_all())

    def _create_model(self):
        '''
        Module class name, module icon and module title
        '''
        model = Gtk.TreeStore(gobject.TYPE_STRING,
                              GdkPixbuf.Pixbuf,
                              gobject.TYPE_STRING)

        return model

    def update_model(self):
        model = self.get_model()
        model.append(None, (None,
                            icon.get_from_name('ubuntu-tweak', size=32),
                            "<b><big>%s</big></b>" % _('Welcome')))

        for category, category_name in MODULE_LOADER.get_categories():
            module_list = MODULE_LOADER.get_modules_by_category(category)

            if module_list:
                iter = model.append(None, (None,
                                           None,
                                           "<b><big>%s</big></b>" % category_name))

                for module in module_list:
                    log.debug("Insert module: name: %s" % module.get_name())

                    model.append(iter, (module.get_name(),
                                        module.get_pixbuf(),
                                        module.get_title()))

    def _add_columns(self):
        column = Gtk.TreeViewColumn('ID',
                                    Gtk.CellRendererText(),
                                    text=self.NAME_COLUMN)
        column.set_visible(False)
        self.append_column(column)

        renderer = Gtk.CellRendererPixbuf()
        column = Gtk.TreeViewColumn("Title")
        column.pack_start(renderer, False)
        column.add_attribute(renderer, 'pixbuf', self.LOGO_COLUMN)
        column.set_spacing(3)
        column.set_cell_data_func(renderer, self.logo_column_view_func, None)

        renderer = Gtk.CellRendererText()
        renderer.set_property('ellipsize', Pango.EllipsizeMode.END)
        column.pack_start(renderer, True)
        column.add_attribute(renderer, 'markup', self.TITLE_COLUMN)
        self.append_column(column)

        column = Gtk.TreeViewColumn()
        column.set_visible(False)
        self.append_column(column)
        self.set_expander_column(column)

    def logo_column_view_func(self, cell_layout, renderer, model, iter, data=None):
        pixbuf = model.get_value(iter, self.LOGO_COLUMN)

        if pixbuf == None:
            renderer.set_property("visible", False)
        else:
            renderer.set_property("visible", True)


class UbuntuTweakApp(Unique.App, GuiBuilder):
    def __init__(self, name='com.ubuntu-tweak.Tweak', startup_id=''):
        Unique.App.__init__(self, name=name, startup_id=startup_id)
        GuiBuilder.__init__(self, file_name='mainwindow.ui')

        module_view = ModuleTreeView()
        self.scrolledwindow1.add(module_view)

        self.tweaknotebook.append_page(WelcomePage(), Gtk.Label(label=_('Welcome')))

        self.watch_window(self.mainwindow)
        self.connect('message-received', self.on_message_received)

        self.mainwindow.show_all()

    def on_mainwindow_destroy(self, widget):
        Gtk.main_quit()

    def on_about_button_clicked(self, widget):
        self.aboutdialog.set_version(VERSION)
        self.aboutdialog.set_transient_for(self.mainwindow)
        self.aboutdialog.run()
        self.aboutdialog.destroy()

    def on_message_received(self, app, command, message, time):
        log.debug("on_message_received: command: %s, message: %s, time: %s" % (
            command, message, time))
        if command == Unique.Command.ACTIVATE:
            self.mainwindow.present()

        return False

    def run(self):
        Gtk.main()