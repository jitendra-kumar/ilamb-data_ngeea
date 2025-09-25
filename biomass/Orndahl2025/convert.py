import rasterio
import numpy as np
import netCDF4 as nc
import sys

def geotiff_to_netcdf(biomass_tif, landfrac_tif, netcdf_file, resolution):
    # Step 1: Read the GeoTIFF file using rasterio
    with rasterio.open(biomass_tif) as dataset:
        # Read metadata and band data
        transform = dataset.transform
        band1_data = dataset.read(1)  
        nodata_value = dataset.nodata  
        height, width = band1_data.shape  
        print(transform)
        # We will access individual coefficients from the transform to
        # assemble coordinates
        a = transform.a  # x-scale (pixel width)
        b = transform.b  # x-skew
        c = transform.c  # x-origin (top-left x coordinate)
        d = transform.d  # y-skew
        e = transform.e  # y-scale (pixel height, usually negative)
        f = transform.f  # y-origin (top-left y coordinate)
        print(f"height: {height} width: {width} a: {a}, b: {b}, c: {c}, d: {d}, e: {e}, f: {f}")

        # Extract the coordinate arrays from the transform
        lon_vals = np.array([((transform.c + transform.a/2) + transform.a * i) for i in range(width)])
        lat_vals = np.array([(transform.f + transform.e/2) + transform.e * j for j in range(height)])

        # Create bounds for each grid cell
        pixel_width = abs(transform.b)  # Each pixel's width
        pixel_height = abs(transform[5])  # Each pixel's height

        lon_bounds = np.stack([lon_vals - pixel_width / 2, lon_vals + pixel_width / 2], axis=-1)
        lat_bounds = np.stack([lat_vals - pixel_height / 2, lat_vals + pixel_height / 2], axis=-1)

        # Replace NoData values with np.nan for consistency
        if nodata_value is not None:
            band1_data = np.where(band1_data == nodata_value, np.nan, band1_data)

    # read landfrac data
    # assuming the landfrac has same size and extent as biomass but
    # should add a check here -- ToDo 
    with rasterio.open(landfrac_tif) as dataset2:
        landfrac_data = dataset2.read(1)
        nodata_value_landfrac = dataset2.nodata  # Extract the NoData value
        # Replace NoData values with np.nan for consistency
        if nodata_value_landfrac is not None:
            landfrac_data = np.where(landfrac_data == nodata_value_landfrac, np.nan, landfrac_data)

    # Step 2: Write the NetCDF file
    with nc.Dataset(netcdf_file, "w", format="NETCDF4") as nc_file:
        # Define dimensions
        lat_dim = nc_file.createDimension("lat", len(lat_vals))
        lon_dim = nc_file.createDimension("lon", len(lon_vals))
        nv = nc_file.createDimension("nv", 2)  # For bounds variables

        # Create variables for latitudes, longitudes, and their bounds
        lat_var = nc_file.createVariable("lat", "f4", ("lat",))
        lon_var = nc_file.createVariable("lon", "f4", ("lon",))
        lat_bnds_var = nc_file.createVariable("lat_bnds", "f4", ("lat", "nv"))
        lon_bnds_var = nc_file.createVariable("lon_bnds", "f4", ("lon", "nv"))

        # Create a variable for biomass data (from biomass band 1 from tif file)
        biomass_var = nc_file.createVariable("biomass", "f4", ("lat", "lon"), fill_value=np.nan)

        lat_var.units = "degrees_north"
        lon_var.units = "degrees_east"
        biomass_var.units = "g m-2"  
        lat_var.standard_name = "latitude"
        lon_var.standard_name = "longitude"
        biomass_var.long_name = "biomass"
        

       # Add _FillValue for biomass variable
        if nodata_value is not None:
            biomass_var.setncatts({"_FillValue": np.float32(np.nan)})


        # Create a variable for landfrac data (from landfrac band 1 from tif file)
        landfrac_var = nc_file.createVariable("landfrac", "f4", ("lat", "lon"), fill_value=np.nan)
        landfrac_var.units = "percent"  
        landfrac_var.long_name = "land area fraction"
 
       # Add _FillValue for landfrac variable
        if nodata_value_landfrac is not None:
            landfrac_var.setncatts({"_FillValue": np.float32(np.nan)})

        # Assign data to NetCDF variables
        lat_var[:] = lat_vals
        lon_var[:] = lon_vals
        lat_bnds_var[:, :] = lat_bounds
        lon_bnds_var[:, :] = lon_bounds
        biomass_var[:, :] = band1_data
        landfrac_var[:, :] = landfrac_data

        # Add metadata
#       nc_file.title = "Aboveground Biomass from Orndahl et. al. 2025 processed to 0.25 degree resolution."
#       nc_file.title = "Aboveground Biomass from Orndahl et. al. 2025 processed to 0.10 degree resolution."
#       nc_file.title = "Aboveground Biomass from Orndahl et. al. 2025 processed to 0.01 degree resolution."
        nc_file.title = f"Aboveground Biomass from Orndahl et. al. 2025 processed to {resolution} degree resolution."
        nc_file.source = "Orndahl et. al. 2025. Gridded 30-meter resolution estimates of aboveground plant biomass, woody plant biomass and woody plant dominance across the Arctic tundra biome (2020). doi:10.18739/A2NS0M06B"
        nc_file.references = "Orndahl, K. M., Berner, L. T., Macander, M. J., Arndal, M. F., Alexander, H. D., Humphreys, E. R., Loranty, M. M., Ludwig, S. M., Nyman, J., Juutinen, S., Aurela, M., Mikola, J., Mack, M. C., Rose, M., Vankoughnett, M. R., Iversen, C. M., Kumar, J., Salmon, V. G., Yang, D., … Goetz, S. J. (2025). Next generation Arctic vegetation maps: Aboveground plant biomass and woody dominance mapped at 30 m resolution across the tundra biome. Remote Sensing of Environment, 323, 114717. https://doi.org/10.1016/j.rse.2025.114717"

if __name__ == "__main__":
    # Define input GeoTIFF file and output NetCDF file
#   biomass_tif = "merged_plant_agb_2020_p500_EPSG4326_025d_float32.tif"  
#   landfrac_tif = "fraction_valid_025d.tif"
#   netcdf_file = "plant_agb_2020_p500_EPSG4326_025d_float32.nc"    

#   biomass_tif = "merged_plant_agb_2020_p500_EPSG4326_010d_float32.tif"  
#   landfrac_tif = "fraction_valid_010d.tif"
#   netcdf_file = "plant_agb_2020_p500_EPSG4326_010d_float32.nc"    

#   biomass_tif = "merged_plant_agb_2020_p500_EPSG4326_0010d_float32.tif"  
#   landfrac_tif = "fraction_valid_0010d.tif"
#   netcdf_file = "plant_agb_2020_p500_EPSG4326_0010d_float32.nc"    

    biomass_tif = sys.argv[1]
    landfrac_tif = sys.argv[2]
    netcdf_file = sys.argv[3]
    resolution = float(sys.argv[4])

    geotiff_to_netcdf(biomass_tif, landfrac_tif, netcdf_file, resolution)

