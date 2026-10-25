import numpy as np
from sklearn.neural_network import BernoulliRBM
from sklearn.preprocessing import StandardScaler

# -------------------------------------------------
# RBM Hidden Representation - Travel Booking Data
# -------------------------------------------------

# Visible variables:
# Beach, Mountain, City, Budget, Luxury, Weekend
X = np.array([
    [1,0,0,1,0,1],
    [1,0,0,0,1,1],
    [0,1,0,1,0,0],
    [0,1,0,0,1,0],
    [0,0,1,1,0,1],
    [0,0,1,0,1,1],
    [1,0,0,1,0,0],
    [0,1,0,1,0,1],
    [0,0,1,0,1,0],
    [1,0,0,0,1,0],
    [0,1,0,0,1,1],
    [0,0,1,1,0,0]
], dtype=float)

features = ["Beach", "Mountain", "City", "Budget", "Luxury", "Weekend"]

# Train a small RBM
rbm = BernoulliRBM(
    n_components=3,
    learning_rate=0.08,
    batch_size=4,
    n_iter=80,
    random_state=42,
    verbose=False
)
rbm.fit(X)

# Hidden representation for each booking
H = rbm.transform(X)

print("RBM HIDDEN REPRESENTATION - TRAVEL BOOKING PROJECT")
print("=" * 55)
print("Visible features:", ", ".join(features))
print("Hidden units: 3")
print()

print("Hidden representations:")
for i, row in enumerate(H, start=1):
    print(f"Booking {i:02d}: H1={row[0]:.3f}, H2={row[1]:.3f}, H3={row[2]:.3f}")

# Explain each hidden unit using the strongest positive weights
print("\nHidden-unit feature associations:")
for j in range(rbm.components_.shape[0]):
    weights = rbm.components_[j]
    order = np.argsort(weights)[::-1]
    top = [(features[k], weights[k]) for k in order[:3]]
    print(f"H{j+1}: " + ", ".join(f"{name} ({weight:.3f})" for name, weight in top))

# Test a new booking observation
new_booking = np.array([[1, 0, 0, 0, 1, 1]], dtype=float)
new_hidden = rbm.transform(new_booking)[0]
print("\nNew booking:", dict(zip(features, new_booking[0].astype(int))))
print("New hidden representation:", np.round(new_hidden, 3))

print("\nInterpretation:")
print("Hidden units are learned features that summarize combinations of booking variables.")
print("A high hidden-unit value means that the booking pattern strongly activates that learned feature.")