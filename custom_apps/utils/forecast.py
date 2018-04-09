def forecast(vendor_settings, snowfall, storm_days, has_ice):
    """
    Performs the super-cool work forecast computation to estimate the number of projected salts and plow trips after a
    storm

    :param vendor_settings: A VendorSettings instance containing the parameters needed for this computation
    :param snowfall:        Number of inches of snowfall
    :param storm_days:      Number of days of storm
    :param has_ice:         Whether the storm had ice
    :return:                A dict with keys salts and plws
    """
    nsalts = storm_days // 3 + 1
    nplows = min(snowfall // 4, 1)
    if has_ice:
        nsalts *= 2
    nsalts *= vendor_settings.const_a
    nplows *= vendor_settings.const_b

    return {'salts': nsalts, 'plows': nplows}
