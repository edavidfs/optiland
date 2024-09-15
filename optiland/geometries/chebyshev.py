import numpy as np
from optiland.geometries.newton_raphson import NewtonRaphsonGeometry


class ChebyshevPolynomialGeometry(NewtonRaphsonGeometry):
    """
    Represents a Chebyshev polynomial geometry defined as:

    z = r^2 / (R * (1 + sqrt(1 - (1 + k) * r^2 / R^2))) +
        sum(Cij * T_i(x / norm_x) * T_j(y / norm_y))

    where
    - r^2 = x^2 + y^2
    - R is the radius of curvature
    - k is the conic constant
    - Cij are the Chebyshev polynomial coefficients
    - T_i(x) is the Chebyshev polynomial of the first kind of degree i
    - norm_x and norm_y are normalization factors for the x and y coordinates

    The coefficients are defined in a 2D array where coefficients[i][j] is the
    coefficient for T_i(x) * T_j(y).

    Args:
        coordinate_system (str): The coordinate system used for the geometry.
        radius (float): The radius of curvature of the geometry.
        conic (float, optional): The conic constant of the geometry.
            Defaults to 0.0.
        tol (float, optional): The tolerance value used in calculations.
            Defaults to 1e-10.
        max_iter (int, optional): The maximum number of iterations used in
            calculations. Defaults to 100.
        coefficients (list or np.ndarray, optional): The coefficients of the
            Chebyshev polynomial surface. Defaults to an empty list, indicating
            no Chebyshev polynomial coefficients are used.
        norm_x (int, optional): The normalization factor for the x-coordinate.
            Defaults to 1.
        norm_y (int, optional): The normalization factor for the y-coordinate.
            Defaults to 1.
    """

    def __init__(self, coordinate_system, radius, conic=0.0,
                 tol=1e-10, max_iter=100, coefficients=[], norm_x=1, norm_y=1):
        super().__init__(coordinate_system, radius, conic, tol, max_iter)
        self.c = np.atleast_2d(coefficients)
        self.norm_x = norm_x
        self.norm_y = norm_y

    def sag(self, x=0, y=0):
        """
        Calculates the sag of the Chebyshev polynomial surface at the given
        coordinates.

        Args:
            x (float, np.ndarray, optional): The x-coordinate(s).
                Defaults to 0.
            y (float, np.ndarray, optional): The y-coordinate(s).
                Defaults to 0.

        Returns:
            float: The sag value at the given coordinates.
        """
        x_norm = x / self.norm_x
        y_norm = y / self.norm_y

        if np.any(np.abs(x_norm) > 1) or np.any(np.abs(y_norm) > 1):
            raise ValueError('Chebyshev input coordinates must be normalized '
                             'to [-1, 1]. Consider updating the normalization '
                             'factors.')

        r2 = x**2 + y**2
        z = r2 / (self.radius *
                  (1 + np.sqrt(1 - (1 + self.k) * r2 / self.radius**2)))

        non_zero_indices = np.argwhere(self.c != 0)
        for i, j in non_zero_indices:
            z += (self.c[i, j] *
                  self._chebyshev(i, x_norm) * self._chebyshev(j, y_norm))

        return z

    def _surface_normal(self, x, y):
        """
        Calculates the surface normal of the Chebyshev polynomial surface at
        the given x and y position.

        Args:
            x (np.ndarray): The x values to use for calculation.
            y (np.ndarray): The y values to use for calculation.

        Returns:
            tuple: The surface normal components (nx, ny, nz).
        """
        x_norm = x / self.norm_x
        y_norm = y / self.norm_y

        if np.any(np.abs(x_norm) > 1) or np.any(np.abs(y_norm) > 1):
            raise ValueError('Chebyshev input coordinates must be normalized '
                             'to [-1, 1]. Consider updating the normalization '
                             'factors.')

        r2 = x**2 + y**2
        denom = self.radius * np.sqrt(1 - (1 + self.k)*r2 / self.radius**2)
        dzdx = x / denom
        dzdy = y / denom

        non_zero_indices = np.argwhere(self.c != 0)
        for i, j in non_zero_indices:
            dzdx += (self._chebyshev_derivative(i, x_norm) *
                     self.c[i, j] * self._chebyshev(j, y_norm))
            dzdy += (self._chebyshev_derivative(j, y_norm) *
                     self.c[i, j] * self._chebyshev(i, x_norm))

        norm = np.sqrt(dzdx**2 + dzdy**2 + 1)
        nx = -dzdx / norm
        ny = -dzdy / norm
        nz = 1 / norm

        return nx, ny, nz

    def _chebyshev(self, n, x):
        """
        Calculates the Chebyshev polynomial of the first kind of degree n at
        the given x value.

        Args:
            n (int): The degree of the Chebyshev polynomial.
            x (np.ndarray): The x value to use for calculation.

        Returns:
            np.ndarray: The Chebyshev polynomial of the first kind of degree n
                at the given x value.
        """
        return np.cos(n * np.arccos(x))

    def _chebyshev_derivative(self, n, x):
        """
        Calculates the derivative of the Chebyshev polynomial of the first kind
        of degree n at the given x value.

        Args:
            n (int): The degree of the Chebyshev polynomial.
            x (np.ndarray): The x value to use for calculation.

        Returns:
            np.ndarray: The derivative of the Chebyshev polynomial of the first
                kind of degree n at the given x value.
        """
        return n * np.sin(n * np.arccos(x)) / np.sqrt(1 - x**2)