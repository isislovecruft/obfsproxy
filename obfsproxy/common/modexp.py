import gmpy

def powMod( x, y, mod ):
    """
    Efficiently calculate and return `x' to the power of `y' mod `mod'.

    Before the modular exponentiation, the three numbers are converted to
    GMPY's bignum representation which speeds up exponentiation.
    """

    x = gmpy.mpz(x)
    y = gmpy.mpz(y)
    mod = gmpy.mpz(mod)

    return pow(x, y, mod)
