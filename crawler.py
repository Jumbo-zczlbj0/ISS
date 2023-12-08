# import carla
# import numpy as np
# from scipy.spatial.transform import Rotation as R
# from matplotlib import pyplot as plt
# import open3d as o3d

# # 连接到CARLA服务器
# client = carla.Client('localhost', 2000)
# client.set_timeout(10.0)
# world = client.get_world()

# # 选择一个车辆蓝图
# blueprint_library = world.get_blueprint_library()
# vehicle_bp = blueprint_library.filter('model3')[0]

# # 设置车辆的初始位置
# spawn_point = carla.Transform(carla.Location(x=230, y=195, z=40), carla.Rotation(yaw=180))
# vehicle = world.spawn_actor(vehicle_bp, spawn_point)

# # 设置LIDAR传感器
# lidar_bp = blueprint_library.find('sensor.lidar.ray_cast')
# lidar_bp.set_attribute('channels', '32')
# lidar_bp.set_attribute('range', '50')
# lidar_bp.set_attribute('rotation_frequency', '20')
# lidar_bp.set_attribute('upper_fov', '10')
# lidar_bp.set_attribute('lower_fov', '-30')
# lidar_location = carla.Location(0, 0, 2)  # 在车顶上
# lidar_transform = carla.Transform(lidar_location)
# lidar_sensor = world.spawn_actor(lidar_bp, lidar_transform, attach_to=vehicle)

# # 处理LIDAR数据
# import numpy as np
# import os

# def process_lidar_data(data):
#     # 将原始LIDAR数据转换为点云
#     points = np.frombuffer(data.raw_data, dtype=np.dtype('f4'))
#     points = np.reshape(points, (int(points.shape[0] / 4), 4))
#     visualize_lidar_data(points, data)

#     # # 丢弃强度信息，只保留位置坐标
#     # points = points[:, :3]

#     # # 将点云数据保存为OFF/PLY文件
#     # # save_to_ply(points, 'lidar_points.ply')
#     # save_to_off(points, 'lidar_data_{}.off'.format(data.frame))

# def visualize_lidar_data(points, data):

#     pcd = o3d.geometry.PointCloud()
#     pcd.points = o3d.utility.Vector3dVector(points[:, :3])

#     # 可视化点云
#     o3d.visualization.draw_geometries([pcd])

# def save_to_ply(points, filename):
#     with open(filename, 'w') as f:
#         f.write("ply\n")
#         f.write("format ascii 1.0\n")
#         f.write("element vertex {}\n".format(len(points)))
#         f.write("property float x\n")
#         f.write("property float y\n")
#         f.write("property float z\n")
#         f.write("end_header\n")
#         for point in points:
#             f.write("{} {} {}\n".format(point[0], point[1], point[2]))

# def save_to_off(points, filename):
#     with open(filename, 'w') as file:
#         # 写入OFF文件头
#         file.write('OFF\n')
#         # 写入顶点数、面数和边数
#         file.write(f'{len(points)} 0 0\n')
        
#         # 写入顶点数据
#         for p in points:
#             file.write(f'{p[0]} {p[1]} {p[2]}\n')

# # 监听LIDAR数据
# lidar_sensor.listen(lambda data: process_lidar_data(data))

# try:
#     # 运行一段时间来收集数据
#     world.wait_for_tick(10)
# finally:
#     # 清理
#     lidar_sensor.destroy()
#     vehicle.destroy()

# # 请记得在使用完成后销毁车辆和传感器
# # vehicle.destroy()
# # lidar_sensor.destroy()

import sys
import time

import carla
import open3d as o3d
import numpy as np
import random
from matplotlib import cm
from datetime import datetime

VIDIDIS = np.array(cm.get_cmap("plasma").colors)
VID_RANGE = np.linspace(0.0, 1.0, VIDIDIS.shape[0])

def generate_lidar_bp(blueprint_library, delta):
    """
    To get lidar bp
    :param blueprint_library: the world blueprint_library
    :param delta: update rate(s)
    :return: lidar bp
    """
    lidar_bp = blueprint_library.find("sensor.lidar.ray_cast")
    lidar_bp.set_attribute("dropoff_general_rate", "0.0")
    lidar_bp.set_attribute("dropoff_intensity_limit", "1.0")
    lidar_bp.set_attribute("dropoff_zero_intensity", "0.0")

    lidar_bp.set_attribute("upper_fov", str(15.0))
    lidar_bp.set_attribute("lower_fov", str(-25.0))
    lidar_bp.set_attribute("channels", str(64.0))
    lidar_bp.set_attribute("range", str(100.0))
    lidar_bp.set_attribute("rotation_frequency", str(1.0 / delta))
    lidar_bp.set_attribute("points_per_second", str(500000))
    # lidar_bp = blueprint_library.find('sensor.lidar.ray_cast')
    # lidar_bp.set_attribute('channels', '32')
    # lidar_bp.set_attribute('range', '50')
    # lidar_bp.set_attribute('rotation_frequency', '20')
    # lidar_bp.set_attribute('upper_fov', '10')
    # lidar_bp.set_attribute('lower_fov', '-30')
    # lidar_location = carla.Location(0, 0, 2)  # 在车顶上
    # lidar_transform = carla.Transform(lidar_location)
    # lidar_sensor = world.spawn_actor(lidar_bp, lidar_transform, attach_to=vehicle)

    return lidar_bp


def lidar_callback(point_cloud, point_list):
    # We need to convert point cloud(carla-format) into numpy.ndarray
    data = np.copy(np.frombuffer(point_cloud.raw_data, dtype = np.dtype("f4")))
    data = np.reshape(data, (int(data.shape[0] / 4), 4))

    intensity = data[:, -1]
    intensity_col = 1.0 - np.log(intensity) / np.log(np.exp(-0.004 * 100))
    int_color = np.c_[
        np.interp(intensity_col, VID_RANGE, VIDIDIS[:, 0]),
        np.interp(intensity_col, VID_RANGE, VIDIDIS[:, 1]),
        np.interp(intensity_col, VID_RANGE, VIDIDIS[:, 2])]

    points = data[:, :-1] # we only use x, y, z coordinates
    points[:, 1] = -points[:, 1] # This is different from official script
    point_list.points = o3d.utility.Vector3dVector(points)
    point_list.colors = o3d.utility.Vector3dVector(int_color)

    # store point cloud into .off file
    o3d.io.write_point_cloud("point_cloud_{}.ply".format(point_cloud.frame), point_list)



if __name__ == "__main__":
    client = carla.Client("127.0.0.1", 2000)
    client.set_timeout(2.0)
    world = client.get_world()

    try:
        # 1. To do some synchronous settings in world
        original_settings = world.get_settings()
        settings = world.get_settings()
        traffic_manager = client.get_trafficmanager(8000)
        traffic_manager.set_synchronous_mode(True)

        delta = 0.05

        settings.fixed_delta_seconds = delta
        settings.synchronous_mode = True
        # settings.no_rendering_mode = True
        world.apply_settings(settings)

        # 2. To get blueprint for your ego vehicle and spawn it!
        blueprint_library = world.get_blueprint_library()
        vehicle_bp = blueprint_library.filter("model3")[0]
        vehicle_transform = random.choice(world.get_map().get_spawn_points())
        vehicle = world.spawn_actor(vehicle_bp, vehicle_transform)
        vehicle.set_autopilot(True)

        # 3. To get lidar blueprint and spawn it on your car!
        lidar_bp = generate_lidar_bp(blueprint_library, delta)
        lidar_transform = carla.Transform(carla.Location(z = 1.8))
        lidar = world.spawn_actor(lidar_bp, lidar_transform, attach_to = vehicle)

        # 4. We set a point_list to store our point cloud
        point_list = o3d.geometry.PointCloud()

        # 5. Listen to the lidar to collect point cloud
        lidar.listen(lambda data: lidar_callback(data, point_list))

        # 6. We set some basic settings for display with open3d
        vis = o3d.visualization.Visualizer()
        vis.create_window(
            window_name= "Display Point Cloud",
            width= 960,
            height= 540,
            left= 480,
            top= 270)

        vis.get_render_option().background_color = [0.05, 0.05, 0.05]
        vis.get_render_option().point_size = 1
        vis.get_render_option().show_coordinate_frame = True

        frame = 0
        dt0 = datetime.now()

        while frame < 100:
            if frame == 2:
                vis.add_geometry(point_list)

            vis.update_geometry(point_list)
            vis.poll_events()
            vis.update_renderer()
            time.sleep(0.005)

            world.tick()

            # We here add a spectator to watch how our ego vehicle will move
            spectator = world.get_spectator()
            transform = vehicle.get_transform()  # we get the transform of vehicle
            spectator.set_transform(carla.Transform(transform.location + carla.Location(z=50),
                                                    carla.Rotation(pitch=-90)))


            process_time = datetime.now() - dt0
            sys.stdout.write("\r" + "FPS: " + str(1.0 / process_time.total_seconds()) + "Current Frame: " + str(frame))
            sys.stdout.flush()
            dt0 = datetime.now()

            frame += 1

    finally:
        world.apply_settings(original_settings)
        traffic_manager.set_synchronous_mode(False)
        vehicle.destroy()
        lidar.destroy()
        vis.destroy_window()