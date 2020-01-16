bl_info = {
	"name": "Rubik's Cube Add-on",
	"description": "Creating and dealing with Rubik's cube",
	"author": "mic19",
	"version": (0, 0, 1),
	"blender": (2, 80, 0),
	"location": "3D View > Tools",
	"warning": "",
	"wiki_url": "",
	"tracker_url": "",
	"category": "Development"
}


import bpy, math, mathutils, copy
from enum import Enum
from math import radians
from mathutils import Matrix, Vector


def clear_material(material):
	if material.node_tree:
		material.node_tree.links.clear()
		material.node_tree.nodes.clear()


def compare_vects(vec1, vec2, tol=0.1):
	if vec2[0] - tol > vec1[0] or vec1[0] > vec2[0] + tol:
		return False

	if vec2[1] - tol > vec1[1] or vec1[1] > vec2[1] + tol:
		return False

	if vec2[2] - tol > vec1[2] or vec1[2] > vec2[2] + tol:
		return False

	return True


def round_vect(vec, digits):
	return Vector((round(vec[0], digits), round(vec[1], digits), round(vec[2], digits)))


###############################################################
# Strategy design pattern #####################################
class CubeBlockBuilder():
	def __init__(self):
		pass

	# Method to create building block in Rubik's Cube
	def create(self, x, y, z):
		pass

	def color(self, cube_name, left = None, right = None, forward = None, back = None, top = None, bottom = None):
		pass


class PrimitiveCubeStrategy(CubeBlockBuilder):
	def __init__(self, size = 0.9):
		self.size = size

		self.direction_dict = {
			"left": mathutils.Vector((-1, 0, 0)),
			"right": mathutils.Vector((1, 0, 0)),
			"forward": mathutils.Vector((0, 1, 0)),
			"back": mathutils.Vector((0, -1, 0)),
			"top": mathutils.Vector((0, 0, 1)),
			"bottom": mathutils.Vector((0, 0, -1))
		}

		# Create materials to use
		self.color_dict = {
			"Default": (0.0146095, 0.0146095, 0.0146095, 1),
			"Yellow": (0.8, 0.680115, 0.0146383, 1),
			"Red": (0.8, 0.00767614, 0.0320392, 1),
			"Green": (0.0136964, 0.8, 0.11931, 1),
			"Blue": (0.0468122, 0.0778236, 0.8, 1),
			"Orange": (0.8, 0.180169, 0.0181465, 1),
			"White": (0.564415, 0.462877, 0.468984, 1)
		}

		self.material_dict = {}

		for key in self.color_dict:
			material_name = "MaterialCube" + key
			material = bpy.data.materials.get(material_name)

			if not material:
				material = bpy.data.materials.new(material_name)
			clear_material(material)

			bpy.data.materials[material_name].use_nodes = True
			material = bpy.data.materials[material_name]

			output_node = material.node_tree.nodes.new(type="ShaderNodeOutputMaterial")
			diffuse_node = material.node_tree.nodes.new(type="ShaderNodeBsdfDiffuse")
			link_to_output = material.node_tree.links.new(diffuse_node.outputs["BSDF"], output_node.inputs["Surface"])
			diffuse_node.inputs[0].default_value = self.color_dict[key]
			material.use_nodes = True

			self.material_dict[material_name] = material

	def create(self, x, y, z):
		bpy.ops.mesh.primitive_cube_add(size=self.size, location=(x, y, z))

	def color(self, cube_name, left = None, right = None, forward = None, back = None, top = None, bottom = None):
		bpy.context.view_layer.objects.active = bpy.data.objects[cube_name]

		# In edit mode
		bpy.ops.object.editmode_toggle()
		import bmesh

		bpy.ops.mesh.select_all(action='SELECT')
		mesh = bpy.context.object.data

		bmesh = bmesh.from_edit_mesh(mesh)

		# Default color
		bpy.data.objects[cube_name].active_material = bpy.data.materials["MaterialCubeDefault"]
		bpy.ops.mesh.select_all(action='DESELECT')

		colors_dict = {
			"left": left,
			"right": right,
			"forward": forward,
			"back": back,
			"top": top,
			"bottom": bottom
		}

		index_dict = {}
		material_index = 1

		for key in colors_dict:
			if colors_dict[key] != None:
				bpy.ops.object.material_slot_add()
				bpy.data.objects[cube_name].active_material = self.material_dict["MaterialCube" + colors_dict[key]]
				index_dict[key] = material_index
				material_index += 1

		for face in bmesh.faces:
			for key in index_dict:
				if compare_vects(face.normal.normalized(), self.direction_dict[key], 0.2) == True:
					face.select = True
					bpy.context.object.active_material_index = index_dict[key]
					bpy.ops.object.material_slot_assign()
					face.select = False

		bmesh.free()
		bpy.ops.object.editmode_toggle()


class FancyCubeStrategy(PrimitiveCubeStrategy):
	def __init__(self):
		super(FancyCubeStrategy, self).__init__(1)

	def create(self, x, y, z):
		cube_name = "CubeName"

		bpy.context.scene.cursor.location = [x, y, z]
		bpy.ops.mesh.primitive_cube_add(size=1)
		cube = bpy.context.object
		cube.name = cube_name

		# Make rounded edges
		bpy.ops.object.modifier_add(type='SUBSURF')
		bpy.context.object.modifiers["Subdivision"].subdivision_type = 'SIMPLE'
		bpy.context.object.modifiers["Subdivision"].render_levels = 4
		bpy.context.object.modifiers["Subdivision"].levels = 4
		bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Subdivision")
		bpy.ops.object.shade_smooth()

		# Helping object
		bpy.ops.mesh.primitive_cube_add(size=self.size / 2)
		cube_shrink = bpy.context.object
		cube_shrink.name = "CubeShrink0"

		bpy.context.view_layer.objects.active = cube
		bpy.ops.object.modifier_add(type='SHRINKWRAP')
		bpy.context.object.modifiers["Shrinkwrap"].target = bpy.data.objects["CubeShrink0"]
		bpy.context.object.modifiers["Shrinkwrap"].offset = 0.25
		bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Shrinkwrap")

		bpy.context.view_layer.objects.active = cube_shrink
		bpy.ops.object.delete()

		bpy.context.view_layer.objects.active = cube


#########################################################


class RubikCube():
	def __init__(self, size, name="RubikCube"):
		self.size = size
		bpy.ops.object.empty_add(type='PLAIN_AXES')

		self.parent_object = bpy.context.object
		self.parent_object.name = name
		# In case the name exists it may become sth like RubikCube.001
		self.parent_object_name = self.parent_object.name

		self.cube_block_builder = FancyCubeStrategy()
		self._build_cube()

		self.temp_angle = 0

	def _build_cube(self):
		iter = 0
		cube_number = 0

		xy_planes = []
		xz_planes = []
		yz_planes = []

		self.locations_list = []
		self.locations_dict = {}

		# remember original cubes position
		xy_loc = {}
		xz_loc = {}
		yz_loc = {}

		for i in range(self.size):
			xy_planes.append([])
			xz_planes.append([])
			yz_planes.append([])

			xy_loc[i] = {}
			xz_loc[i] = {}
			yz_loc[i] = {}

		for z in range(self.size):
			iter += 1
			iter2 = 0
			for y in range(self.size):
				iter2 += 1
				iter3 = 0
				for x in range(self.size):
					self.cube_block_builder.create(iter3 + 1, iter2, iter)
					iter3 += 1

					cube = bpy.context.object
					cube.name = 'Cube' + str(cube_number)
					cube.parent = self.parent_object
					cube_number += 1

					xy_planes[z].append(cube.name)
					xz_planes[y].append(cube.name)
					yz_planes[x].append(cube.name)

					loc = cube.location.copy()
					loc.freeze()

					self.locations_list.append(loc)
					self.locations_dict[loc] = cube.name

					xy_loc[z][loc] = cube.name
					xz_loc[y][loc] = cube.name
					yz_loc[x][loc] = cube.name

		bpy.context.scene.cursor.location = self.parent_object.location

		# 1 color cubes
		for i in range(self.size, self.size * self.size - self.size):
			if not (i % self.size == 0 or i % self.size == self.size - 1):
				self.cube_block_builder.color(xy_planes[self.size - 1][i], top = "Yellow")
				self.cube_block_builder.color(xy_planes[0][i], bottom = "White")
				self.cube_block_builder.color(xz_planes[self.size - 1][i], forward = "Blue")
				self.cube_block_builder.color(xz_planes[0][i], back = "Green")
				self.cube_block_builder.color(yz_planes[0][i], left = "Red")
				self.cube_block_builder.color(yz_planes[self.size - 1][i], right = "Orange")

		# 2 colors cubes
		for i in range(1, self.size - 1):
			# x axis
			self.cube_block_builder.color(xy_planes[self.size - 1][i], back = "Green", top = "Yellow")
			self.cube_block_builder.color(xy_planes[self.size - 1][self.size * self.size - self.size + i], forward = "Blue", top = "Yellow")
			self.cube_block_builder.color(xy_planes[0][i], back = "Green" , bottom = "White")
			self.cube_block_builder.color(xy_planes[0][self.size * self.size - self.size + i], forward = "Blue", bottom = "White")
			# y axis
			self.cube_block_builder.color(xy_planes[self.size - 1][i * self.size], left = "Red", top = "Yellow")
			self.cube_block_builder.color(xy_planes[self.size - 1][self.size - 1 + i * self.size], right = "Orange", top = "Yellow")
			self.cube_block_builder.color(xy_planes[0][i * self.size], left = "Red", bottom = "White")
			self.cube_block_builder.color(xy_planes[0][self.size - 1 + i * self.size], right = "Orange", bottom = "White")
			# z axis
			self.cube_block_builder.color(xy_planes[i][0], left = "Red", back = "Green")
			self.cube_block_builder.color(xy_planes[i][self.size - 1], back = "Green", right = "Orange")
			self.cube_block_builder.color(xy_planes[i][self.size * self.size - 1], forward = "Blue", right = "Orange")
			self.cube_block_builder.color(xy_planes[i][self.size * self.size - self.size], left = "Red", forward = "Blue")

		# 3 colors cubes
		self.cube_block_builder.color(xy_planes[self.size - 1][0], left = "Red", back = "Green", top = "Yellow")
		self.cube_block_builder.color(xy_planes[self.size - 1][self.size - 1], right = "Orange", back = "Green", top = "Yellow")
		self.cube_block_builder.color(xy_planes[self.size - 1][self.size * self.size - self.size], left = "Red", forward = "Blue", top = "Yellow")
		self.cube_block_builder.color(xy_planes[self.size - 1][self.size * self.size - 1], right = "Orange", forward = "Blue", top = "Yellow")

		self.cube_block_builder.color(xy_planes[0][0], left = "Red", back = "Green", bottom = "White")
		self.cube_block_builder.color(xy_planes[0][self.size - 1], right = "Orange", back = "Green", bottom = "White")
		self.cube_block_builder.color(xy_planes[0][self.size * self.size - self.size], left = "Red", forward = "Blue", bottom = "White")
		self.cube_block_builder.color(xy_planes[0][self.size * self.size - 1], right = "Orange", forward = "Blue", bottom = "White")

		self.xy_planes = xy_planes
		self.xz_planes = xz_planes
		self.yz_planes = yz_planes

		self.xy_loc = xy_loc
		self.xz_loc = xz_loc
		self.yz_loc = yz_loc

	def _find_center_point(self):
		x_sum = 0
		y_sum = 0
		z_sum = 0

		for plane in self.xy_planes:
			for cube_name in plane:
				x_sum += bpy.data.objects[cube_name].matrix_world.translation.x
				y_sum += bpy.data.objects[cube_name].matrix_world.translation.y
				z_sum += bpy.data.objects[cube_name].matrix_world.translation.z

		num = self.size * len(self.xy_planes[0])
		return [x_sum / num, y_sum / num, z_sum / num]

	# Rotate face that contains miniature cube (of cube_name) around the axis
	def rotate(self, cube_name, axis, degrees=90):
		dict_items_to_change = {}
		self._update()
		self.center_point = self._find_center_point()

		if degrees % 90 == 0:
			parent_object = bpy.data.objects[self.parent_object_name]

			self.center_point = self._find_center_point()
			origin = Vector(self.center_point)
			# Prepare cursor for rotating around center point
			bpy.context.scene.cursor.rotation_euler = parent_object.rotation_euler
			prev_tool_setting = bpy.context.scene.tool_settings.transform_pivot_point
			bpy.context.scene.cursor.location = origin

			bpy.context.scene.tool_settings.transform_pivot_point = 'CURSOR'
			current_frame = bpy.context.scene.frame_current
			anim_iters = int(degrees / 10)

			if axis == 'X':
				index = self.locations_list.index(bpy.data.objects[cube_name].location)
				start_index = index % self.size

				for i in range(self.size ** 2):
					loc = self.locations_list[start_index + i * self.size]
					name = self.locations_dict[loc]
					bpy.ops.object.select_all(action='DESELECT')
					obj = bpy.data.objects[name]
					obj.select_set(True)

					# Rotate step by step for animation
					for k in range(anim_iters):
						bpy.context.scene.frame_set(current_frame + k)
						bpy.ops.transform.rotate(value=math.radians(10), orient_axis='X', orient_type='CURSOR')
						bpy.ops.anim.keyframe_insert(type='LocRotScale')

					# rotate help object
					obj.location = round_vect(obj.location, 3)
					new_loc = obj.location.copy()
					bpy.ops.anim.keyframe_insert(type='LocRotScale')

					new_loc.freeze()
					dict_items_to_change[new_loc] = name

			if axis == 'Y':
				index = self.locations_list.index(bpy.data.objects[cube_name].location)
				temp = index % (self.size ** 2)
				start_index = int(temp / self.size) * self.size

				for i in range(self.size):
					for j in range(self.size):
						loc = self.locations_list[start_index + i * self.size ** 2 + j]
						name = self.locations_dict[loc]
						bpy.ops.object.select_all(action='DESELECT')
						obj = bpy.data.objects[name]
						obj.select_set(True)

						# Rotate step by step for animation
						for k in range(anim_iters):
							bpy.context.scene.frame_set(current_frame + k)
							bpy.ops.transform.rotate(value=math.radians(10), orient_axis='Y', orient_type='CURSOR')
							bpy.ops.anim.keyframe_insert(type='LocRotScale')

						obj.location = round_vect(obj.location, 3)
						new_loc = obj.location.copy()
						bpy.ops.anim.keyframe_insert(type='LocRotScale')

						new_loc.freeze()
						dict_items_to_change[new_loc] = name

			if axis == 'Z':
				index = self.locations_list.index(bpy.data.objects[cube_name].location)
				start_index = int(index / self.size ** 2) * self.size ** 2

				for i in range(self.size ** 2):
					loc = self.locations_list[start_index + i]
					name = self.locations_dict[loc]
					bpy.ops.object.select_all(action='DESELECT')
					obj = bpy.data.objects[name]
					obj.select_set(True)

					# Rotate step by step for animation
					for k in range(anim_iters):
						bpy.context.scene.frame_set(current_frame + k)
						bpy.ops.transform.rotate(value=math.radians(10), orient_axis='Z', orient_type='CURSOR')
						bpy.ops.anim.keyframe_insert(type='LocRotScale')

					obj.location = round_vect(obj.location, 3)
					new_loc = obj.location.copy()
					bpy.ops.anim.keyframe_insert(type='LocRotScale')

					new_loc.freeze()
					dict_items_to_change[new_loc] = name
		else:
			# TODO: create a method to deal with this rotation
			pass

		bpy.context.scene.frame_set(current_frame + anim_iters)
		bpy.context.scene.cursor.location = parent_object.location
		bpy.context.scene.tool_settings.transform_pivot_point = prev_tool_setting

		bpy.ops.object.select_all(action='SELECT')
		bpy.data.objects[self.parent_object_name].select_set(False)
		bpy.ops.anim.keyframe_insert(type='BUILTIN_KSI_LocRot')

		bpy.ops.object.select_all(action='DESELECT')
		bpy.data.objects[cube_name].select_set(True)

		for key in dict_items_to_change:
			self.locations_dict[key] = dict_items_to_change[key]

	def _update(self):
		bpy.ops.object.select_all(action='SELECT')
		bpy.context.scene.frame_set(bpy.context.scene.frame_current)
		bpy.ops.anim.keyframe_insert(type='LocRotScale')
		bpy.ops.object.select_all(action='DESELECT')


# Usage example
"""
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
a = RubikCube(3)
a.rotate('Cube18', 'X')
"""


from bpy.props import (StringProperty,
					   IntProperty,
					   FloatProperty,
					   FloatVectorProperty,
					   EnumProperty,
					   PointerProperty,
					   )
from bpy.types import (Panel,
					   Operator,
					   PropertyGroup,
					   )


# OPERATORS - Build ###########################################
all_rubik_cubes = []

class OperatorBuildProperties(bpy.types.PropertyGroup):
	size: IntProperty(
		name="Size",
		description="Rubik's cube size",
		default=3,
		min=2,
		max=6
	)


class RC_OT_Build(Operator):
	bl_label = "Build Rubik's Cube"
	bl_idname = "rubik.operator_build"
	bl_options = {'REGISTER', 'UNDO'}

	def execute(self, context):
		global all_rubik_cubes

		size = context.scene.cube_build_props.size
		rubik_cube = RubikCube(size, "RubikCube" + str(len(all_rubik_cubes)))
		all_rubik_cubes.append(rubik_cube)

		bpy.ops.wm.tool_set_by_id(name='builtin.select_box', space_type='VIEW_3D')

		return {'FINISHED'}


# OPERATORS - Rotate ###########################################
class OperatorRotateProperties(bpy.types.PropertyGroup):
	angle: IntProperty(
		name="Angle",
		description="Angle to rotate the Cube's part",
		default=90,
		min=-180,
		max=180
	)

	axis_enum: EnumProperty(
		name="Axis",
		description="Axis to rotate selected cube's part",
		items=[("X", "X", "OP1"),
			   ("Y", "Y", "OP2"),
			   ("Z", "Z", "OP3")
			   ]
	)


class RC_OT_Rotate(Operator):
	bl_label = "Rotate Cube's Face"
	bl_idname = "rubik.operator_rotate"
	bl_options = {'REGISTER', 'UNDO'}

	rubik_cube_to_rotate = None

	def execute(self, context):
		angle = context.scene.cube_rotate_props.angle
		axis = context.scene.cube_rotate_props.axis_enum
		cube_to_rotate = context.active_object

		self.rubik_cube_to_rotate.rotate(cube_to_rotate.name, axis, angle)
		return {'FINISHED'}

	def invoke(self, context, event):
		global all_rubik_cubes
		parent_object = context.active_object.parent
		self.rubik_cube_to_rotate = None

		for rubik_cube in all_rubik_cubes:
			if parent_object.name == rubik_cube.parent_object_name:
				self.rubik_cube_to_rotate = rubik_cube
				break;

		if self.rubik_cube_to_rotate is not None:
			return self.execute(context)
		else:
			return {'CANCELLED'}


# Panel for Rubik's cube ##############################################
class View3DPanel:
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_options = {'DEFAULT_CLOSED'}

	@classmethod
	def poll(cls, context):
		# TODO: checking context like context.object is not None
		return True


class RubikCubeBuildPanel(View3DPanel, bpy.types.Panel):
	bl_idname = "VIEW3D_PT_build_cube"
	bl_label = "Build Rubik's Cube"

	def draw(self, context):
		scene = context.scene

		self.layout.prop(scene.cube_build_props, "size")
		self.layout.operator("rubik.operator_build")

		self.layout.label(text="", icon_value=custom_icons["cube_icon"].icon_id)


class RubikCubeRotatePanel(View3DPanel, bpy.types.Panel):
	bl_idname = "VIEW3D_PT_rotate_cube"
	bl_label = "Rotate Rubik's Cube"

	def draw(self, context):
		scene = context.scene

		self.layout.prop(scene.cube_rotate_props, "angle")
		self.layout.prop(scene.cube_rotate_props, "axis_enum")
		self.layout.operator("rubik.operator_rotate")


classes = (
	RC_OT_Build,
	RC_OT_Rotate,
	OperatorBuildProperties,
	OperatorRotateProperties,
	RubikCubeBuildPanel,
	RubikCubeRotatePanel
)

custom_icons = None


def register():
	# Register icons
	from bpy.utils import register_class, register_tool, previews
	global custom_icons
	import os
	dir_path = os.path.dirname(os.path.realpath(__file__))

	custom_icons = bpy.utils.previews.new()
	icons_dir = dir_path + "icons"
	custom_icons.load("cube_icon", os.path.join(icons_dir, "icon.png"), 'IMAGE')

	for cls in classes:
		register_class(cls)

	bpy.types.Scene.cube_build_props = bpy.props.PointerProperty(type=OperatorBuildProperties)
	bpy.types.Scene.cube_rotate_props = bpy.props.PointerProperty(type=OperatorRotateProperties)


def unregister():
	from bpy.utils import unregister_class, unregister_tool, previews
	global custom_icons
	bpy.utils.previews.remove(custom_icons)

	for cls in reversed(classes):
		unregister_class(cls)

	del bpy.types.Scene.cube_build_props
	del bpy.types.Scene.cube_rotate_props


if __name__ == "__main__":
	register()

