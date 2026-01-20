from .common import build_mc_router

router = build_mc_router(
    db_name="mc3d",
    prefix="/mc3d",
    tag="mc3d",
    methods=["pbe-v1", "pbesol-v1", "pbesol-v2"],
)
