"""
Univariate stochastic volatility (SV) model
"""
from __future__ import division

from numpy.random import rand
import numpy.random as npr
import numpy as np
import scipy.stats as stats

import matplotlib.pyplot as plt

import statlib.distributions as dist
import statlib.ffbs as ffbs
import statlib.plotting as plotting

class SVModel(object):
    """
    Univariate AR(1) stochastic volatility (SV) model using normal approximation
    for observation noise (see notes)

    Parameters
    ----------


    Notes
    -----
    r_t ~ N(0, \sigma_t^2)
    \sigma_t = exp(\mu + x_t)
    x_t = \phi x_{t-1} + \epsilon_t
    \epsilon_t ~ N(0, v)

    y_t = log(r_t^2) / 2
    y_t = \mu + x_t + \nu_t, \nu_t = \log(\kappa_t) / 2
    \kappa_t ~ \chi^2_1

    reparameterize
    y_t = z_t + \nu_t
    z_t = \mu + \phi(z_{t-1} - \mu) + \epsilon_t

    Approximate p(\nu_t) \approx \sum_{j=1}^J q_j N(b_j, w_j)
    Defaults to Kim, Shephard, Chib mixture of 7 components
    """
    def __init__(self, data, nu_approx=None):
        if nu_approx is None:
            nu_approx = get_log_chi2_normal_mix()

        self.nobs = len(data)
        self.data = data

        self.y = np.log(data ** 2) / 2

        self.nu_approx = nu_approx

        self.z, self.gamma, self.mu, self.phi, self.v = (None,) * 5

        # HACK
        self.phi_prior = 1, 0.01
        self.mu_prior = 0, 1
        self.v_prior = self.nobs, 0.002 # a, v_0

    def sample(self, niter=1000, nburn=0, thin=1, debug=False):
        self._setup_storage(niter, thin)

        # mixture component selected
        gamma = np.zeros(self.nobs)
        mu = 0
        phi = 0.9
        v = 0.002
        z = np.zeros(self.nobs + 1) # volatility sequence

        for i in range(-nburn, niter):
            if i % 50 == 0:
                print i

            gamma = self._sample_gamma(z)
            phi = self._sample_phi(phi, z, mu, v)
            mu = self._sample_mu(z, phi, v)
            v = self._sample_v(z, mu, phi)
            z = self._sample_z(gamma, phi, v, mu)

            if i % thin == 0 and i >= 0:
                k = i // thin
                self.gamma[k] = gamma
                self.phi[k] = phi
                self.mu[k] = mu
                self.v[k] = v
                self.z[k] = z

            if debug:
                print 'phi: %10.6f mu: %10.6f v: %10.6f' % (phi, mu, v)

    def _setup_storage(self, niter, thin):
        nresults = niter // thin

        self.z = np.zeros((nresults, self.nobs + 1))
        self.gamma = np.zeros((nresults, self.nobs), dtype=int)

        self.mu = np.zeros(nresults)
        self.phi = np.zeros(nresults)
        self.v = np.zeros(nresults)

    def _sample_gamma(self, z):
        mix = self.nu_approx

        probs = np.empty((len(mix.weights), self.nobs))

        # bleh, slowest part in the whole code
        i = 0
        for q, m, w in zip(mix.weights, mix.means, mix.variances):
            probs[i] = q * np.exp(-0.5*(self.y-m-z[1:])**2 / w) / np.sqrt(w)
            i += 1

        probs /= probs.sum(0)

        return ffbs.sample_discrete(probs.T)

        # return np.apply_along_axis(sample_measure, 0, probs)

    def _sample_phi(self, phi, z, mu, v):
        """
        Sample phi from truncated normal with Metropolis-Hastings acceptance
        step
        """
        # MH step
        prior_m, prior_v = self.phi_prior

        r = z - mu
        sumsq = (r[:-1] ** 2).sum()

        css_mean = (r[1:] * r[:-1]).sum() / sumsq
        css_var = v / sumsq

        prop_var = 1 / (1 / css_var + 1 / prior_v)
        prop_mean = (css_mean / css_var + prior_m / prior_v) * prop_var

        phistar = dist.rtrunc_norm(prop_mean, np.sqrt(prop_var), 0, 1)

        def ln_accept_factor(phi):
            return (0.5 * np.log(1 - phi ** 2) +
                    0.5 * phi ** 2 * (z[0] - mu)**2 / v)

        if np.log(rand()) < ln_accept_factor(phistar) - ln_accept_factor(phi):
            return phistar
        else:
            return phi

    def _sample_mu(self, z, phi, v):
        r"""
        .. math::

            p(\mu | ...) \propto p(\mu) N(z_0 | \mu, v / (1 - \phi^2)
                                 \prod N(z_t | \mu + \phi(z_{t-1} - \mu), v)
        """
        prior_m, prior_var = self.mu_prior

        # From N(z0 | mu, v / (1 - phi^2))
        p2 = (1 - phi**2) / v
        m2 = z[0]

        # From Prod N(z_t | mu + phi(z_t-1 - mu), v)
        p3 = self.nobs * (1 - phi) ** 2 / v
        m3 = (z[1:] - phi * z[:-1]).mean() / (1 - phi)

        # full conditional mean and precision
        fc_prec = 1 / prior_var + p2 + p3
        fc_mean = (prior_m / prior_var + m2 * p2 + m3 * p3) / fc_prec

        return np.random.normal(fc_mean, np.sqrt(1 / fc_prec))

    def _sample_v(self, z, mu, phi):
        r"""

        """
        a_prior, v0 = self.v_prior

        fc_a = (a_prior + self.nobs + 1.) / 2
        fc_b = (a_prior * v0 + (1 - phi**2) * (z[0] - mu)**2
                + ((z[1:] - mu - phi * (z[:-1] - mu)) ** 2).sum()) / 2

        return 1 / npr.gamma(fc_a, scale=1 / fc_b)

    def _sample_z(self, gamma, phi, v, mu):

        Y = self.y - self.nu_approx.means[gamma] - mu
        F = np.ones(self.nobs)
        G = F * phi
        V = self.nu_approx.variances[gamma]
        W = v
        m0 = - mu
        C0 = v / (1 - phi ** 2)

        # FFBS in Cython
        return ffbs.univ_ffbs(Y, F, G, V, W, m0, C0) + mu

    def plot_z(self):
        plt.figure()

        vol = np.exp(self.z)
        for i in range(50):
            k = np.random.randint(len(vol))
            plt.plot(vol[k], '0.5')

        plt.plot(vol.mean(0), 'k')


def sample_measure(weights):
    return weights.cumsum().searchsorted(rand())

def compare_mix_with_logchi2(draws=5000):
    # make a graph showing the mixture approx
    plt.figure()

    mixture = get_log_chi2_normal_mix()

    rv = stats.chi2(1)
    draws = np.log(rv.rvs(5000)) / 2

    plotting.density_plot(draws, style='k--', label=r'$\log(\chi^2_1) / 2$')
    mixture.plot(style='k', label='Mixture')

    plt.legend(loc='best')

def get_log_chi2_normal_mix():
    # Kim, Shephard, Chib (1998) approx of log \chi^2_1
    weights = [0.0073, 0.0000, 0.1056, 0.2575, 0.3400, 0.2457, 0.0440]
    means = [-5.7002, -4.9186, -2.6216, -1.1793, -0.3255, 0.2624, 0.7537]
    variances = [1.4490, 1.2949, 0.6534, 0.3157, 0.1600, 0.0851, 0.0418]
    return dist.NormalMixture(means, variances, weights)

if __name__ == '__main__':
    np.random.seed(1)
    import statlib.datasets as ds


    mixture = get_log_chi2_normal_mix()

    data = ds.fx_gbpusd()
    data = ds.fx_yenusd()

    model = SVModel(data)
    model.sample(1000, nburn=500)
