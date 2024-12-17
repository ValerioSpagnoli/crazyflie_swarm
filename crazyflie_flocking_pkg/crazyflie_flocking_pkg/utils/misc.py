import numpy as np


def get_clipper(v, max):
    clipper = np.linalg.norm(v) / max

    if clipper > 1:
        return clipper
    else:
        return 1


def get_versor(vector):
    # Given a vector, return the versor
    norm_vector = np.linalg.norm(vector)
    if norm_vector < 1e-14:
        print("Error: vector 0, impossible to normalize")
        return vector
    return vector / norm_vector
