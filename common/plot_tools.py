# -*- coding: utf-8 -*-
"""
@author: thoe
"""

import numpy as np
from matplotlib import cm
from matplotlib import pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d import proj3d

def pie_marker(x_data,y_data,distribution,color,z_data=None,linecolor=None,linestyle=None,markersize=10,linewidth=1,ax_handle=None,edgecolors='none'):
    #Originally from https://stackoverflow.com/questions/56337732/how-to-plot-scatter-pie-chart-using-matplotlib
    assert len(distribution) == len(color), "distribution and color do not match in length"
    assert len(x_data) == len(y_data), "x and y is not the same length"

    if ax_handle is None:
        if z_data is None:
            fig, f = plt.subplots()
        else:
            fig = plt.figure()
            f = fig.gca(projection='3d')
    else:
        f = ax_handle
        if z_data is not None:
            assert len(z_data) == len(x_data), "z is not the same length as x and y"

    if linecolor is None:
        linecolor = color[0]
    if linestyle is None:
        if z_data is None:
            f.plot(x_data,y_data,linewidth=linewidth,color=linecolor,zorder=1)
        else:
            f.plot(x_data,y_data,zs=z_data,linewidth=linewidth,color=linecolor,zorder=1)
    else:
        if z_data is None:
            f.plot(x_data,y_data,linestyle=linestyle,linewidth=linewidth,color=linecolor,zorder=1)
        else:
            f.plot(x_data,y_data,zs=z_data,linestyle=linestyle,linewidth=linewidth,color=linecolor,zorder=1)

    integrated_distribution = np.cumsum(distribution)
    norm_integrated_distribution = integrated_distribution/integrated_distribution[-1]
    pie = [0] + norm_integrated_distribution.tolist()

    for start_piece, end_piece, piece_color in zip(pie[:-1],pie[1:],color):
        angles = np.linspace(2*np.pi*start_piece,2*np.pi*end_piece)
        x = [0] + np.cos(angles).tolist()
        y = [0] + np.sin(angles).tolist()
        xy = np.column_stack([x,y])

        if z_data is None:
            f.scatter(x_data,y_data,marker=xy,s=markersize,color=piece_color,edgecolors=edgecolors,zorder=2)
        else:
            f.scatter(x_data,y_data,z_data,marker=xy,s=markersize,color=piece_color,edgecolors=edgecolors,zorder=2,depthshade=False)

    return f

def colormaps()
