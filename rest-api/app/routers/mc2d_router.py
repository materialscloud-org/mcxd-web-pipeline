from .common import build_mc_router

router = build_mc_router(
    db_name="mc2d",
    prefix="/mc2d",
    tag="mc2d",
    methods=["pbe-v1"],
)
