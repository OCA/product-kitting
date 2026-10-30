# Copyright 2026 Tecnativa - Adasat Torres
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


def post_init_hook(env):
    kits = (
        env["product.product"]
        .with_context(active_test=False)
        .search([("is_kits", "=", True)])
    )
    kits._compute_volume()
    kits._compute_weight()
