from .common import build_mc_router

router = build_mc_router(
    db_name="mc1d",
    prefix="/mc1d",
    tag="mc1d",
    methods=["pbe-v1"],
)
