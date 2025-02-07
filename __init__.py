# ==============================================================================
#  Copyright (c) 2022 Thomas Mathieson.
# ==============================================================================

# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####
# <pep8 compliant>

bl_info = {
    "name": "Import OMSI map/cfg/sco/o3d files",
    "author": "Adam/Thomas Mathieson",
    "version": (1, 1, 4),
    "blender": (3, 1, 0),
    "location": "File > Import-Export",
    "description": "Import OMSI model .map, .cfg, .sco, and .o3d files along with their meshes, UVs, and materials",
    "wiki_url": "https://github.com/space928/Blender-O3D-IO-Public",
    "doc_url": "https://github.com/space928/Blender-O3D-IO-Public",
    "tracker_url": "https://github.com/space928/Blender-O3D-IO-Public/issues/new?assignees=&labels=bug%2C+needs"
                   "+triage&template=bug_report.md&title=",
    "category": "Import-Export"
}

from .o3d_io import io_o3d_import, io_o3d_export, io_omsi_tile
import bpy
from mathutils import Matrix

from bpy_extras.io_utils import (
    ImportHelper,
    ExportHelper,
    axis_conversion,
)

from bpy.props import (BoolProperty,
                       FloatProperty,
                       StringProperty,
                       CollectionProperty,
                       IntProperty
                       )


def log(*args):
    print("[O3D_IO]", *args)


def make_annotations(cls):
    """
    Converts class fields to annotations if running with Blender 2.8

    Credit to: https://github.com/CGCookie/blender-addon-updater/pull/49
    :param cls: class to convert
    :return: converted class
    """
    if bpy.app.version < (2, 80):
        return cls
    if bpy.app.version >= (2, 93, 0):
        bl_props = {k: v for k, v in cls.__dict__.items() if isinstance(v, bpy.props._PropertyDeferred)}
    else:
        bl_props = {k: v for k, v in cls.__dict__.items() if isinstance(v, tuple)}
    # bl_props = {k: v for k, v in cls.__dict__.items() if isinstance(v, tuple)}
    if bl_props:
        if '__annotations__' not in cls.__dict__:
            setattr(cls, '__annotations__', {})
        annotations = cls.__dict__['__annotations__']
        for k, v in bl_props.items():
            annotations[k] = v
            delattr(cls, k)
    return cls


class ImportModelCFG(bpy.types.Operator, ImportHelper):
    """Imports an OMSI model file from a CFG, SCO, or O3D file"""
    bl_idname = "import_scene.omsi_model_cfg"
    bl_label = "Import OMSI Model.cfg"
    bl_options = {'PRESET', 'UNDO'}

    # ImportHelper mixin class uses this
    filename_ext = ".o3d"

    filter_glob = StringProperty(
        default="*.cfg;*.sco;*.o3d;*.rdy",
        options={'HIDDEN'},
    )

    import_x = BoolProperty(
        name="Import .x files",
        description="Attempt to import .x files, this can be buggy and only works if you have the correct .x importer "
                    "already installed.",
        default=True,
    )

    override_text_encoding = StringProperty(
        name="Override text encoding (leave blank for default)",
        description="If you are having issues with some letters/accents in object names not importing correctly, try "
                    "adjusting this. Sometimes model cfg files are encoded with an unusual encoding scheme. This "
                    "usually depends on the region/language of the computer used to make the cfg file. For western "
                    "Europe try: 'cp-1252', for Eastern Europe (Cyrillic languages) try: 'cp-1251', for a full list of "
                    "supported encodings check this website: "
                    "https://docs.python.org/3/library/codecs.html#standard-encodings",
        default="",
    )

    hide_lods = BoolProperty(
        name="Hide additional LODs",
        description="Hides any meshes in LODs other than the highest quality one.",
        default=True,
    )

    # Selected files
    files = CollectionProperty(type=bpy.types.PropertyGroup)

    def execute(self, context):
        """
        Imports the selected CFG/SCO/O3D file
        :param context: blender context
        :return: success message
        """
        context.window.cursor_set('WAIT')
        io_o3d_import.do_import(self.filepath, context, self.import_x, self.override_text_encoding, self.hide_lods)
        context.window.cursor_set('DEFAULT')

        return {'FINISHED'}


#if not (bpy.app.version[0] < 3 and bpy.app.version[1] < 80):
#    @orientation_helper(axis_forward='Y', axis_up='Z')
class ExportModelCFG(bpy.types.Operator, ExportHelper):
    """Imports an OMSI model file from a CFG, SCO, or O3D file"""
    bl_idname = "export_scene.omsi_model_cfg"
    bl_label = "Export OMSI Model.cfg"

    filename_ext = ".o3d"
    check_extension = None

    filter_glob = StringProperty(
        default="*.cfg;*.sco;*.o3d",
        options={'HIDDEN'},
    )
    use_selection = BoolProperty(
        name="Selection Only",
        description="Export selected objects only",
        default=True,
    )
    global_scale = FloatProperty(
        name="Scale",
        min=0.01,
        max=1000.0,
        default=1.0,
    )
    o3d_version = IntProperty(
        name="O3D Version",
        min=1,
        max=7,
        default=7,
    )

    def execute(self, context):
        context.window.cursor_set('WAIT')

        global_matrix = Matrix.Scale(self.global_scale, 4)
        io_o3d_export.do_export(self.filepath, context, global_matrix, self.use_selection, self.o3d_version)

        context.window.cursor_set('DEFAULT')

        return {'FINISHED'}

    #def draw(self, context):
    #    layout = self.layout
    #    layout.use_property_split = True
    #    layout.use_property_decorate = False
    #    sfile = context.space_data
    #    operator = sfile.active_operator
    #    # col = layout.column(heading="Format")
    #    # col.prop(operator, "use_ascii")


class ImportOMSITile(bpy.types.Operator, ImportHelper):
    """Imports an OMSI map file from a .map/.cfg file"""
    bl_idname = "import_scene.omsi_tile"
    bl_label = "Import OMSI tile.map/global.cfg"
    bl_options = {'PRESET', 'UNDO'}

    # ImportHelper mixin class uses this
    filename_ext = ".map"

    filter_glob = StringProperty(
        default="*.map;*.cfg",
        options={'HIDDEN'},
    )

    import_scos = BoolProperty(
        name="Import SCOs",
        description="Import the SCO files",
        default=False
    )

    import_splines = BoolProperty(
        name="Import Splines",
        description="Import the map's splines",
        default=False
    )

    spline_tess_dist = FloatProperty(
        name="Spline Tesselation Precision",
        description="The minimum distance between spline segments",
        min=0.1,
        max=1000.0,
        default=6.0,
    )

    spline_curve_sag = FloatProperty(
        name="Spline Tesselation Curve Precision",
        description="The minimum sag distance between the curve and the tessellated segment. Note that this is used in "
                    "combination with the above setting, whichever is lower is used by the tessellator.",
        min=0.0005,
        max=1.0,
        default=0.005,
    )

    import_x = BoolProperty(
        name="Import .x Files",
        description="Attempt to import .x files, this can be buggy and only works if you have the correct .x importer "
                    "already installed.",
        default=True,
    )

    # Selected files
    files = CollectionProperty(type=bpy.types.PropertyGroup)

    def execute(self, context):
        """
        Imports the selected map file
        :param context: blender context
        :return: success message
        """
        context.window.cursor_set('WAIT')
        io_omsi_tile.do_import(context, self.filepath, self.import_scos, self.import_splines, self.spline_tess_dist,
                               self.spline_curve_sag, self.import_x)
        context.window.cursor_set('DEFAULT')

        return {'FINISHED'}


def menu_func_import(self, context):
    self.layout.operator(ImportModelCFG.bl_idname, text="OMSI Model Config (*.cfg, *.sco, *.o3d)")


def menu_func_export(self, context):
    self.layout.operator(ExportModelCFG.bl_idname, text="OMSI Model Config (*.cfg, *.sco, *.o3d)")


def menu_func_import_tile(self, context):
    self.layout.operator(ImportOMSITile.bl_idname, text="OMSI Map Tile (*.map)")


classes = [
    ImportModelCFG,
    ExportModelCFG,
    ImportOMSITile
]


def register():
    for cls in classes:
        cls = make_annotations(cls)
        bpy.utils.register_class(cls)

    # Compat with 2.7x and 3.x
    if bpy.app.version[0] < 3 and bpy.app.version[1] < 80:
        bpy.types.INFO_MT_file_import.append(menu_func_import)
        bpy.types.INFO_MT_file_export.append(menu_func_export)
        bpy.types.INFO_MT_file_import.append(menu_func_import_tile)
    else:
        bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
        bpy.types.TOPBAR_MT_file_export.append(menu_func_export)
        bpy.types.TOPBAR_MT_file_import.append(menu_func_import_tile)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    # Compat with 2.7x and 3.x
    if bpy.app.version[0] < 3 and bpy.app.version[1] < 80:
        bpy.types.INFO_MT_file_import.remove(menu_func_import)
        bpy.types.INFO_MT_file_export.remove(menu_func_export)
        bpy.types.INFO_MT_file_import.remove(menu_func_import_tile)
    else:
        bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
        bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
        bpy.types.TOPBAR_MT_file_import.remove(menu_func_import_tile)


if __name__ == "__main__":
    register()
