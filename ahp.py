import numpy as np
from numpy.linalg import eig


def calculate_ahp_weights(criteria_pairs):
    criteria = ['location', 'comfort', 'service', 'treatment', 'food', 'price']

    n = len(criteria)
    matrix = np.ones((n, n))

    for i in range(n):
        for j in range(i + 1, n):
            key = f"{criteria[i]}_vs_{criteria[j]}"
            if key not in criteria_pairs:
                raise KeyError(f"Missing comparison for {key}")
            value = float(criteria_pairs[key])
            matrix[i, j] = value
            matrix[j, i] = 1 / value

    eigenvalues, eigenvectors = eig(matrix)
    max_idx = np.argmax(eigenvalues)
    weights = np.real(eigenvectors[:, max_idx])
    weights = weights / np.sum(weights)

    lambda_max = np.max(eigenvalues)
    ci = (lambda_max - n) / (n - 1)
    ri = {1: 0, 2: 0, 3: 0.58, 4: 0.9, 5: 1.12}.get(n, 1.24)
    cr = ci / ri

    return {criteria[i]: float(weights[i]) for i in range(n)}, float(cr)
