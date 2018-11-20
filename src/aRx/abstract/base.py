class Base:
    def __str__(self) -> str:
        return f"{type(self).__qualname__}"

    def __repr__(self) -> str:
        return (
            f"<{type(self).__qualname__}: "
            + (
                ", ".join(
                    [
                        f"{key}={repr(val)}"
                        for key, val in vars(self).items()
                        if not key.startswith("_")
                    ]
                )
            )
            + ">"
        )
