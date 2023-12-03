from cat.mad_hatter.decorators import hook, tool
import numpy as np 
import matplotlib.pyplot as plt
from datetime import datetime

@tool(return_direct=True)
def get_plot_intent2(input, cat):
    '''get plot'''
    values = np.random.randint(1, 10, 5)
    fig, ax = plt.subplots()
    indici = np.arange(len(values))
    ax.bar(indici, values, color='blue')
    ax.set_xlabel('Index')
    ax.set_ylabel('Value')
    ax.set_title('Random Graph')
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    fig.savefig(f'cat/static/plot-{timestamp}.svg')
    return f"<img style='width:400px' src='http://localhost:1865/static/plot-{timestamp}.svg'>"

@tool(return_direct=True)
def get_image(input, cat):
    '''get image'''
    return "<img style='width:400px' src='https://maxdam.github.io/cat-pizza-challenge/img/thumb.jpg'>"
