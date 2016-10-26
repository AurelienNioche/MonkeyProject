from pylab import np, plt


class Model(object):

    def __init__(self):

        self.reward_max = 1

    @staticmethod
    def softmax(diff, tau):

        """Compute softmax values for each sets of scores in x."""
        # print("x", x)
        # return np.exp(x / tau) / np.sum(np.exp(x / tau), axis=0)
        return 1/(1+np.exp(-(1/tau)*diff))

    def u(self, x, r):

        """Compute utility for a single output considering a parameter of risk-aversion"""
        if x > 0:
            return (x/self.reward_max) ** (1-r)
        elif x == 0:
            return 0
        else:
            raise Exception("Reward can not be negative")

    def U(self, L, r, alpha):

        # print("L", L)
        p, v = L[0], L[1]
        y = self.w(p, alpha) * self.u(v, r)

        # y = 0
        # for p, v in L:
        #     print(p, v)
        #
        #     y += p * cls.u(v, r)
        return y

    @staticmethod
    def w(p, alpha):

        return np.exp(-(-np.log(p))**alpha)


def plot_u(r, monkey, figure_folder):

    m = Model()

    x = np.arange(0, 1.001, 0.001)

    y = [m.u(i, r) for i in x]
    plt.title("Utility function for " + monkey + " with $r = $" +
              "${}$".format(r) + r" [$u(x) = x^{1-r}$]" +"\n")
    plt.plot(x, y, linewidth=3.0, color=(0., 0., 0))
    plt.xlabel("$x$", fontsize=16)
    plt.ylabel("$u(x)$", fontsize=16)

    fig_name = "{}/{}_utility_function.pdf".format(figure_folder, monkey)
    plt.savefig(fig_name)
    plt.close()


def plot_softmax(tau, monkey, figure_folder):

    m = Model()

    x = np.arange(-1.0, 1.001, 0.001)

    y = [m.softmax(i, tau) for i in x]
    plt.title("Softmax function for " + monkey + " with $\\tau = $" + "${}$".format(tau) +
              " [$p(L_0) = 1/(1+e^{-(U(L_0)-U(L_1)) / \\tau})$]" + "\n")
    plt.plot(x, y, linewidth=3.0, color=(0., 0., 0))
    plt.xlabel("$U(L_0) - U(L_1)$", fontsize=16)
    plt.ylabel("$p(L_0)$", fontsize=16)
    plt.xlim([-1, 1])

    fig_name = "{}/{}_softmax_function.pdf".format(figure_folder, monkey)
    plt.savefig(fig_name)
    plt.close()


def plot_w(alpha, monkey, figure_folder):

    m = Model()

    x = np.arange(0, 1.001, 0.001)

    y = [m.w(i, alpha) for i in x]
    plt.title(
        "Probability distortion function for " + monkey + r" with $\alpha = $" + "${}$".format(alpha) +
        r" [$w(p) = e^{-(-\ln_p)^\alpha}$]" + "\n")
    plt.plot(x, y, linewidth=3.0, color=(0., 0., 0))
    plt.xlabel("$p$", fontsize=16)
    plt.ylabel("$w(p)$", fontsize=16)

    fig_name = "{}/{}_probability_distortion.pdf".format(figure_folder, monkey)
    plt.savefig(fig_name)
    plt.close()


def plot_functions(monkey, r, tau, alpha, figure_folder):

    plot_u(r=r, monkey=monkey, figure_folder=figure_folder)
    plot_softmax(tau=tau, monkey=monkey, figure_folder=figure_folder)
    plot_w(alpha=alpha, monkey=monkey, figure_folder=figure_folder)


def main():

    figure_folder = "../figures"

    r = -0.02
    tau = 0.09
    alpha = 0.94
    monkey = "Havane"

    plot_functions(monkey=monkey, r=r, tau=tau, alpha=alpha, figure_folder=figure_folder)

    r = -0.63
    tau = 0.09
    alpha = 1.0
    monkey = "Gladys"

    plot_functions(monkey=monkey, r=r, tau=tau, alpha=alpha, figure_folder=figure_folder)


if __name__ == "__main__":

    main()
