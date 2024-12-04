# stuff
A personal repository of functions that I have used more than once.



Content
  
  
  apps - soon to be a collection of apps. For now it is just one
    
    QMS fitting - compilation of QMS-fitting functions from stuff.scientific.QMS
  
  
  common - more generic coding-tools
    
    admin - functionality for running python-scripts as adminstrator on WinOS
      isUserAdmin, runAsAdmin, test
    
    filters - different filters for data treatment
      smooth, median_filter, rolling_median_filter, low_pass_filter, bin_data, derivative, integrate
    
    import_tools - tools for navigating folders and importing data-files
      find_file, find_directory, load_data_with_names, load_data_sheet_with_names, load_data_sheet, load_delimited_data
    
    plot_tools - only one really cool function, namely a function for plotting customizable pie-charts into a graph
      pie_marker

    stuff - the rest. And the hilarious import-statement "from stuff.common.stuff import fancy"
      fancy, gauss, fermi, format_of_file, name_of_file, time_stamp_str, progress_bar

  
  equipment - drivers for physical equipment. Some are only test-functions for communication with equipment, and not functional drivers. All drivers are written object-oriented, so the equipment configure as its own object.

    AAFG_MFG2110 - no real driver. Just a prompt for the hardware name

    dataq_DI2008 - fully functional driver of the digital-input card from Dataq
      comm, device_name, start, stop, reset, packet_size, srate, decimal, set_filter, add_voltage_analog_channel, ready_statement, read

    leadfluid_BT101L - fully functional driver of the peristaltic LeadFluid pump BT101L
      read, write, read_status, start, stop, read_direction, read_unit, set_unit, flow, set_flow

    omega_cn7800 - functional driver for runnign the Omega CN7800 heater-controller as a simple single-step controller
      temperature, setpoint, set_setpoint, upper_limit, status, start, stop

  
  math - meant to keep generic math-tools. It was introduced to late however, and many of such tools are written somewhere else in stuff

    simple - very simple functions
      isfloat, round_to_nearest

    statistics - statistical tools
      rsqr, linear_fit_plot


  scientific - the core of the stuff-package. It holds by far the most work. It is automated functions for making data-analysis for several kind of physical experiments, microscopy and spectroscopy

    EIS - electrochemical impedance spectroscopy
      format_e, IV, EIS_figure, set_equal_aspect, aesthetics, plot, draw, EIS_data, find_keys, find_Rs, find_Rtot, find_Rp, normalize, Nyquist, Nyquist_curve, EIS_datafile, ADIS_cal, Real, Imag, dReal, dImag

    Microscopy - mostly Energy Dispersive X-rays
      spectroscopy, init_amu_colormap, init_edx_library, get_color_by_element, get_color_by_Z, load_edx, load_eels, OXINST_findlabels, edx_spectrum, edx_lineplot, TIA, plot_edx_linescan, convert_image_to_file

    QMS - Quadropole Mass Spectroscopy
      find_file, find_directory, load_qms_asc, read_SAC, read_RGA_prism_dat, mass_library, correct_air, spectrum_fit, load_data, retrieve_spectrum, set_max_mass, generate_gas_mass_list, add_gas, remove_gas, generated_mass_spectrum, fit_gas_spectrum, fit_time_data, calibrate_currents, write_to_file, run_sequence

    XAS - Xray Absorption Spectroscopy
      find_binding_energy, calibrate_edge, normalise_fluorescence, XANES_linear_combination_fitting

    XRD - Xray Diffraction
      read_xrdml_wavelength, read_xrdml_pattern, read_xrdml_temp, read_xrdml_measurement_time, common, inverse_length, scherrer, spectral_angle_splitting, angle_200, FWHM_200, skewed_lorentzian_fitting, skewed_lorentz, background, func, find_FWHM, find_max_and_median, fit_to_data, pack_the_info, new_xrd_fitting, lorentz, gaussian, pseudo_voigt, background, fcc, bcc, func, fit_to_data, xrd_fitting, lorentz, gaussian, pseudo_voigt, background, fcc, bcc, func, fit_to_data

------------------

Use what you like at your own discretion :)

Thomas, last entry 2024
      
