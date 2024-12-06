import numpy as np


def point_line_distance(point, line_point, direction_vector):
    """
    Calculates the minimum distance between a point and a line in 3D space.

    :param point: Coordinates of the point (x, y, z)
    :param line_point: A point on the line (x0, y0, z0)
    :param direction_vector: Direction vector of the line (a, b, c) with magnitude 1
    :return: Minimum distance between the point and the line
    """
    # Vectors
    P = np.array(point)
    P0 = np.array(line_point)
    v = np.array(direction_vector)

    # Vector P0P
    P0P = P - P0

    # Cross product v x P0P
    cross_product = np.cross(v, P0P)

    # Magnitude of the cross product
    cross_product_magnitude = np.linalg.norm(cross_product)

    # Minimum distance
    distance = cross_product_magnitude
    return distance
