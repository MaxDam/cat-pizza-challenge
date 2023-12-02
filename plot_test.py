from cat.mad_hatter.decorators import hook, tool
import base64
from io import BytesIO
import numpy as np
import matplotlib.pyplot as plt


@tool(return_direct=True)
def get_plot_intent(input, cat):
    '''get plot'''
    x = np.arange(0, 2*np.pi, 0.1)
    y = np.sin(x)
    fig, ax = plt.subplots()
    ax.plot(x, y)
    ax.set_xlabel('x')
    ax.set_ylabel('y')
    ax.set_title('Sinusoid')
    tmpfile = BytesIO()
    fig.savefig(tmpfile, format='png')
    encoded = base64.b64encode(tmpfile.getvalue()).decode('utf-8')
    html = "<img src='data:image/png;base64,{}'>".format(encoded)
    return html


@tool(return_direct=True)
def get_image(input, cat):
    '''get image'''
    return "<img style='width:400px' src='https://maxdam.github.io/cat-pizza-challenge/img/thumb.jpg'>"
