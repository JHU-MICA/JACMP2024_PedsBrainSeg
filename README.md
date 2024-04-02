# Deep Learning Segmentation of Organs-At-Risk with Integration into Clinical Workflow for Pediatric Brain Radiotherapy

Journal of Applied Clinical Medical Physics, 2024

## Getting Started
The pretrained model can be downloaded from:  `https://github.com/JHU-MICA/JACMP2024_PedsBrainSeg/releases/download/Model/model.pt`. This model was trained for the segmentation of the frontal white matter, corpus callosum,
hippocampus, temporal lobes, and brainstem on a pediatric dataset. 

Creating env and installing dependencies:

`conda env create -f environment.yml`

`conda activate JACMP_PedsBrain `

## Monitoring Incoming Files
`dicom_listener.py` : This script continuously monitors a specified port for incoming DICOM series as long as the script is running.

We define a `handle_store` function that saves incoming DICOM files to the patient subdir located in `root` (you need to modify this root)

The rest of script initializes an AE (the AI server hosting the trained model) defined for all storage SOP classes. You should add the IP address of your server as `str` and port number as `int` on `line 28`. 

## Model Inference, Saving Prediction, and Sending DICOM RT
`main.py`: This script has two main functions: `process_dicoms` and `send_dicoms`. Each function is automatically triggered upon new file creation in the dirs `path` and `path2` as long as the script is running. This is done by the python watchdog package.

`process_dicoms` first converts the received DICOM series to NIFTI files using the `DicomRT` tool. It then loads the pretrained model (here UNesT
but it could be replaced by any DL model) and performs inference using the `MONAI SlidingWindowInferer`. The predicted segmentation is then converted from numpy to DICOM RT and saved to `./Dicom_sender` directory.
Saving the DICOM RT to `./Dicom_sender` automatically triggers `send_dicoms`.

`send_dicoms`: instantiates connection between the AI server and TPS and sends output DICOM RT to TPS. You need to add the TPS IP, port, and AE title `line 33`.
Also need to replace `Dicom_sender` path 

## In Summary

For the code to run, you will need to change the following:

On your Workstation:
1) Create a Dicom_sender dir
2) Create a Dicom_receiver dir
3) Create a parent dir for these two subdirs and add its path to `working_dir` line 71 of `main.py`

In `dicom_listener.py`: 

1) The IP (as `str`) and port number (as `int`) line 29
2) The `root` in `handle_store for the `Dicom_receiver` dir 

In `main.py`:
1) `path` is the dir where DICOMs are received from the TPS (`Dicom_receiver`)
2) `path2` is the dir where output DICOM RT are saved (`Dicom_sender`)
3) `pretrained_dict`  path to the pretrained model
4) IP, port number, and AE title of TPS in `send_dicoms`



## In addition

If you need to keep everything running continuously, you can create a batch file calling both `main.py` and `dicom_listener`
and add this batch to Windows `Task scheduler` and configure so that the script is launched on computer startup. This will allow users to send MR series from TPS to server and receive predictions at any time. 

## References

Please cite the following paper.
For whole segmentation pipeline including integration to TPS (dicom_listener.py, main.py):
> Mekki, L., Acharya, A., Ladra, M, Lee, J. (2024). Deep Learning Segmentation of Organs-At-Risk with Integration into Clinical Workflow for Pediatric Brain Radiotherapy. Journal of Applied Clinical Medical Physics, Volume 25, Issue 3, p.e14310. https://doi.org/10.1002/acm2.14310

Relevant papers for models used in this study:

UNesT model ( files from https://monai.io/model-zoo.html are: nest_transformer_3D.py, patchEmbed3D.py, unest_base_patch_4.py, unest_block.py, utils.py)
> Yu, X., Tang, Y., Zhou, Y., Gao, R., Yang, Q., Lee, H. H., Li, T., Bao, S., Huo, Y., Xu, Z., Lasko, T. A., Abramson, R. G., & Landman, B. A. (2023). UNesT: Local spatial representation learning with hierarchical transformer for efficient medical segmentation, Medical Image Analysis, Volume 90. https://doi.org/10.1016/j.media.2023.102939.

Conversion of predictions to DICOM RT (files from: https://github.com/brianmanderson/Dicom_RT_and_Images_to_Mask are ReaderWriter.py, key_list.txt, template_RS.dcm) 
> Anderson, B. M., Wahid, K. A., & Brock, K. K. (2021). Simple Python Module for Conversions Between DICOM Images and Radiation Therapy Structures, Masks, and Prediction Arrays. Practical Radiation Oncology, 11(3), 226–229. https://doi.org/https://doi.org/10.1016/j.prro.2021.02.003




