def powMod( x, y, mod ):
    """
    (Efficiently) Calculate and return `x' to the power of `y' mod `mod'.

    If possible, the three numbers are converted to GMPY's bignum
    representation which speeds up exponentiation.  If GMPY is not installed,
    built-in exponentiation is used.
    """

    try:
        import gmpy
        x = gmpy.mpz(x)
        y = gmpy.mpz(y)
        mod = gmpy.mpz(mod)
    except ImportError:
        # gmpy is not installed but that doesn't matter.
        pass
    finally:
        return pow(x, y, mod)
