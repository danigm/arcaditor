# -*- coding: utf-8 -*-
import os
import pygtk
pygtk.require('2.0')
import gtk, gobject, cairo
import math
import rsvg
pi = math.pi

BLACK = (0.0,0.0,0.0)
WHITE = (1.0,1.0,1.0)


class Arcadiobject:
    def __init__(self, x=0, y=0, w=0, h=0):
        self.width = w
        self.height = h
        self.x = x
        self.y = y

    def scale(self, w=0, h=0):
        self.width = w
        self.height = h

    def move(self, x, y):
        self.x = x
        self.y = y


class SVG(Arcadiobject):
    def __init__(self, directory, **kwargs):
        Arcadiobject.__init__(self, **kwargs)
        self.directory = directory
        self.parts = ['foot', 'body', 'head', 'hair', 'eye']
        self.svgs = self.init_svg()
        self.svg = dict((k, self.svgs[k][0]) for k in self.svgs)
        self.partindex = 0

    def next_part(self):
        self.partindex = (self.partindex + 1) % len(self.parts)

    def prev_part(self):
        self.partindex = (self.partindex - 1) % len(self.parts)

    def next_obj(self):
        part = self.parts[self.partindex]
        objlist = self.svgs[part]
        objindex = objlist.index(self.svg[part])
        objindex = (objindex + 1) % len(objlist)
        self.svg[part] = objlist[objindex]

    def prev_obj(self):
        part = self.parts[self.partindex]
        objlist = self.svgs[part]
        objindex = objlist.index(self.svg[part])
        objindex = (objindex - 1) % len(objlist)
        self.svg[part] = objlist[objindex]

    def init_svg(self):
        svg = {}
        for part in self.parts:
            svg[part] = os.listdir(os.path.join(self.directory, part))
        return svg

    def get_svg(self, part):
        return os.path.join(self.directory, part, self.svg[part])

    def draw(self, cr, export=False):
        if not export:
            x, y = self.x, self.y
        else:
            x, y = 0, 0
        cr.translate(x, y)
        for i, part in enumerate(self.parts):
            if i == self.partindex:
                viewingpart = part
            svg = rsvg.Handle(self.get_svg(part))
            ws, hs = self.scale_svg(svg)
            cr.scale(ws, hs)
            svg.render_cairo(cr)
            cr.scale(1/ws,1/hs)

        if not export:
            cr.mask(cairo.SolidPattern(0,0,0,0.5))
            part = viewingpart
            svg = rsvg.Handle(self.get_svg(part))
            ws, hs = self.scale_svg(svg)
            cr.scale(ws, hs)
            svg.render_cairo(cr)
            cr.scale(1/ws,1/hs)

        cr.translate(-x, -y)

    def scale_svg(self, svg):
        w, h = svg.props.width, svg.props.height
        if not self.width or not self.height:
            self.width, self.height = w, h

        w_scale = self.width / float(w)
        h_scale = self.height / float(h)
        return w_scale, h_scale


class DArea(gtk.DrawingArea):
    def __init__(self):
        gtk.DrawingArea.__init__(self)
        self.connect("expose-event", self.expose)

        self.add_events(gtk.gdk.BUTTON_PRESS_MASK |
                        gtk.gdk.KEY_PRESS_MASK |
                        gtk.gdk.BUTTON1_MOTION_MASK)

        self.connect("expose_event", self.expose)
        self.connect("button_press_event", self.pressing)
        self.connect("key_press_event", self.keypress)
        self.connect("motion_notify_event", self.moving)

        self.arcadio = SVG("arcadio")

    def expose(self, widget, event):
        w, h = self.allocation.width, self.allocation.height
        self.arcadio.x = w / 2 - self.arcadio.width / 2
        self.arcadio.y = h / 2 - self.arcadio.height / 2

        self.context = self.window.cairo_create()

        self.context.rectangle(event.area.x, event.area.y,
                        event.area.width, event.area.height)
        self.context.clip()

        self.draw(self.context, *self.window.get_size())

    def export(self, filename):
        surface = cairo.SVGSurface(filename, self.arcadio.width,
                self.arcadio.height)
        context = cairo.Context(surface)
        self.draw(context, *self.window.get_size(), export=True)

    def draw(self, cr, width, height, export=False):
        if not export:
            cr.set_source_rgb(*WHITE)
            cr.rectangle(0, 0, width, height)
            cr.fill()

        self.arcadio.draw(cr, export)

    def keypress(self, widget, event):
        print "key", event.keyval

    def pressing(self, widget, event):
        print "pressing", event.x, event.y

    def moving(self, widget, event):
        print "moving", event.x, event.y


def clicked_cb(button, *args, **kwargs):
    print "clicked"


def part_prev_cb(button, darea, status):
    darea.arcadio.prev_part()
    update(darea, status)


def part_next_cb(button, darea, status):
    darea.arcadio.next_part()
    update(darea, status)


def obj_prev_cb(button, darea, status):
    darea.arcadio.prev_obj()
    update(darea, status)


def obj_next_cb(button, darea, status):
    darea.arcadio.next_obj()
    update(darea, status)


def update(darea, status):
    gtk.Widget.queue_draw_area (darea, 0, 0,
            darea.allocation.width,
            darea.allocation.height)

    part = darea.arcadio.parts[darea.arcadio.partindex]
    msg = "%s - %s" % (part, darea.arcadio.svg[part])
    status.push(0, msg)

def export_cb(button, darea, status):
    dialog = gtk.FileChooserDialog("export arcadio",
            action=gtk.FILE_CHOOSER_ACTION_SAVE,
            buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK))

    response = dialog.run()
    if response == gtk.RESPONSE_OK:
        filename = dialog.get_filename()
        darea.export(filename)
    dialog.destroy()


def main():
    w = gtk.Window()
    w.set_title("Arcaditor")
    w.set_default_size(500, 300)
    darea = DArea()
    status = gtk.Statusbar()

    vbox = gtk.VBox()
    partbutton1 = gtk.Button("prev", gtk.STOCK_GO_UP)
    partbutton1.connect("clicked", part_prev_cb, darea, status)
    partbutton2 = gtk.Button("next", gtk.STOCK_GO_DOWN)
    partbutton2.connect("clicked", part_next_cb, darea, status)
    partbuttons = gtk.HBox(True)
    partbuttons.add(partbutton1)
    partbuttons.add(partbutton2)
    vbox.add(partbuttons)

    button1 = gtk.Button("prev", gtk.STOCK_GO_BACK)
    button1.connect("clicked", obj_prev_cb, darea, status)
    button2 = gtk.Button("next", gtk.STOCK_GO_FORWARD)
    button2.connect("clicked", obj_next_cb, darea, status)
    buttons = gtk.HBox(True)
    buttons.pack_start(button1)
    buttons.add(button2)
    vbox.add(buttons)

    export = gtk.Button("export")
    export.connect("clicked", export_cb, darea, status)
    vbox.add(export)

    paned = gtk.HPaned()
    paned.pack1(darea, True, True)
    paned.pack2(vbox, False, True)

    vbox = gtk.VBox()
    vbox.add(paned)
    vbox.pack_start(status, False)

    w.add(vbox)
    w.show_all()
    w.connect('destroy', gtk.main_quit)

    update(darea, status)
    gtk.main()

if __name__ == '__main__':
    main()
