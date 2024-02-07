import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
import matplotlib.animation as animation

class ControlledAnimation:
    def __init__(self, fig, animate, frames=100, interval=100, init=None):
        self.fig = fig
        self.init = init
        self.animate = animate
        self.frames = frames
        self.interval = interval
        self.ani = animation.FuncAnimation(self.fig, self.animate, init_func=self.init, frames=self.frames, interval=self.interval)

    def start(self):
        plt.show()

    def stop(self):
        self.ani.event_source.stop()