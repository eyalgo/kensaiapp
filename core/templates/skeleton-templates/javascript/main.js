// The composition root — the only place that wires concrete implementations to abstractions.
// It owns wiring, not flow, and is the only node in the dependency graph that knows a given
// concrete implementation exists. This skeleton ships it empty: a product's own modules,
// and the wiring between them, come from the SDD's § 3 parts table, read per product by the
// launcher that copies this tree.

export async function main() {
  // A product's modules wire in here as they are added.
}
