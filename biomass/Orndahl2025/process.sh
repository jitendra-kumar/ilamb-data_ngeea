#!/bin/bash

MERGE_RASTERS=0
REPROJECT_AND_REGRID_RASTER=0
CREATE_FRACTIONAL_LANDMASK=0

if [ $MERGE_RASTERS -eq 1 ]
then
  time gdal_merge.py -ot UInt16 -n 65535 -a_nodata 65535 -o merged_plant_agb_2020_p500.tif --optfile p500.list
fi

if [ $REPROJECT_AND_REGRID_RASTER -eq 1 ]
then
  # I will do this as two step process:
  # Step 1 -- reprojected the original merged data to EPSG:4326 
  # Step 2 -- regrid using gdalwrap. 
  # Using this two step process so I can be sure of pixel size in lat/lon going in to regrid step
  # Step 1 - reproject
  time gdalwarp -wm 64G  -srcnodata 65535 -dstnodata 65535 -tr square -s_srs EPSG:3571 -t_srs EPSG:4326 -overwrite merged_plant_agb_2020_p500.tif merged_plant_agb_2020_p500_EPSG4326.tif
 # Step 2 - regrid 
  time gdalwarp -ot Float32 -wm 9000 -srcnodata 65535 -dstnodata 65535 -s_srs EPSG:4326 -t_srs EPSG:4326 -te -180 45 180 90 -tr 0.25 0.25 -r average -et 0 -overwrite merged_plant_agb_2020_p500_EPSG4326.tif merged_plant_agb_2020_p500_EPSG4326_025d_float32.tif
  time gdalwarp -ot Float32 -wm 9000 -srcnodata 65535 -dstnodata 65535 -s_srs EPSG:4326 -t_srs EPSG:4326 -te -180 45 180 90 -tr 0.10 0.10 -r average -et 0 -overwrite merged_plant_agb_2020_p500_EPSG4326.tif merged_plant_agb_2020_p500_EPSG4326_010d_float32.tif
  time gdalwarp -ot Float32 -wm 9000 -srcnodata 65535 -dstnodata 65535 -s_srs EPSG:4326 -t_srs EPSG:4326 -te -180 45 180 90 -tr 0.01 0.01 -r average -et 0 -overwrite merged_plant_agb_2020_p500_EPSG4326.tif merged_plant_agb_2020_p500_EPSG4326_0010d_float32.tif


## reproject and regrid in single step -- this works but not using this anymore 
# time gdalwarp -ot Float32 -wm 9000 -srcnodata 65535 -dstnodata 65535 -s_srs EPSG:3571 -t_srs EPSG:4326 -te -180 45 180 90 -tr 0.25 0.25 -r average -et 0 -overwrite merged_plant_agb_2020_p500.tif plant_agb_2020_p500_merged_EPSG4326_025d_float32.tif
# time gdalwarp -ot UInt16 -wm 9000 -srcnodata 65535 -dstnodata 65535 -s_srs EPSG:3571 -t_srs EPSG:4326 -te -180 45 180 90 -tr 0.10 0.10 -r average -et 0 -overwrite merged_plant_agb_2020_p500.tif plant_agb_2020_p500_merged_EPSG4326_010d.tif
# time gdalwarp -ot Float32 -wm 9000 -srcnodata 65535 -dstnodata 65535 -s_srs EPSG:3571 -t_srs EPSG:4326 -te -180 45 180 90 -tr 0.10 0.10 -r average -et 0 -overwrite merged_plant_agb_2020_p500.tif plant_agb_2020_p500_merged_EPSG4326_010d_float32.tif
fi

if [ $CREATE_FRACTIONAL_LANDMASK -eq 1 ]
then
  # create a binary mask
  gdal_calc.py -A merged_plant_agb_2020_p500_EPSG4326.tif --outfile=mask.tif --calc="1*(A!=65535)" --type=Byte --NoDataValue=0 --overwrite

  # resample mask to target resolution using sum method -- this gives us count of valid/land pixels
  time gdalwarp -ot Float32 -wm 9000 -srcnodata 0 -dstnodata -9999 -s_srs EPSG:4326 -t_srs EPSG:4326 -te -180 45 180 90 -tr 0.25 0.25 -r sum -et 0 -overwrite mask.tif sum_resampled_EPSG4326_025d.tif
  time gdalwarp -ot Float32 -wm 9000 -srcnodata 0 -dstnodata -9999 -s_srs EPSG:4326 -t_srs EPSG:4326 -te -180 45 180 90 -tr 0.10 0.10 -r sum -et 0 -overwrite mask.tif sum_resampled_EPSG4326_010d.tif
  time gdalwarp -ot Float32 -wm 9000 -srcnodata 0 -dstnodata -9999 -s_srs EPSG:4326 -t_srs EPSG:4326 -te -180 45 180 90 -tr 0.01 0.01 -r sum -et 0 -overwrite mask.tif sum_resampled_EPSG4326_0010d.tif
 
  # Calculate fraction
  xres=0.25
  yres=0.25
  source_xres=0.000793832476876
  source_yres=0.000793832476876
  gdal_calc.py -A sum_resampled_EPSG4326_025d.tif --outfile=fraction_valid_025d.tif --calc="(A/(${xres}/${source_xres} * ${yres}/${source_yres}))" --type=Float32
  python convert.py merged_plant_agb_2020_p500_EPSG4326_025d_float32.tif fraction_valid_025d.tif plant_agb_2020_p500_EPSG4326_025d_float32.nc 0.25
  
  xres=0.10
  yres=0.10
  source_xres=0.000793832476876
  source_yres=0.000793832476876
  gdal_calc.py -A sum_resampled_EPSG4326_010d.tif --outfile=fraction_valid_010d.tif --calc="(A/(${xres}/${source_xres} * ${yres}/${source_yres}))" --type=Float32
  python convert.py merged_plant_agb_2020_p500_EPSG4326_010d_float32.tif fraction_valid_010d.tif plant_agb_2020_p500_EPSG4326_010d_float32.nc 0.10

  xres=0.010
  yres=0.010
  source_xres=0.000793832476876
  source_yres=0.000793832476876
  gdal_calc.py -A sum_resampled_EPSG4326_0010d.tif --outfile=fraction_valid_0010d.tif --calc="(A/(${xres}/${source_xres} * ${yres}/${source_yres}))" --type=Float32
  python convert.py merged_plant_agb_2020_p500_EPSG4326_0010d_float32.tif fraction_valid_0010d.tif plant_agb_2020_p500_EPSG4326_0010d_float32.nc 0.01
fi


