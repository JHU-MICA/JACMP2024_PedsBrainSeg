import time
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
import nibabel as nib
from monai.inferers import SlidingWindowInferer
from unest_base_patch_4 import UNesT
import shutil
import nibabel.processing as nip
import numpy as np
import torch
import monai.transforms as transforms
import os
import SimpleITK as sitk
from ReaderWriter import DicomReaderWriter
from pydicom import dcmread
from pynetdicom import AE, debug_logger
from pynetdicom.sop_class import RTStructureSetStorage

def mkdir(path):
    if not os.path.exists(path):
        os.makedirs(path)



def send_dicoms(event):

    debug_logger()
    # Initialise the Application Entity
    ae = AE()
    # Add a requested presentation context
    ae.add_requested_context(RTStructureSetStorage)
    # Associate with peer AE, give IP, port number as int, and AE title
    assoc = ae.associate("TPS IP", int('TPS Port'), ae_title='TPS AE Tile')
    if assoc.is_established:
        if 'RS' in event.src_path:
            time.sleep(15)
            dataset = dcmread(event.src_path)
            print('connected')
            status = assoc.send_c_store(dataset)
        assoc.release()
        for f in os.listdir(r"YOUR PATH TO \Dicom_sender"):
            os.remove(os.path.join(r"YOUR PATH TO \Dicom_sender", f))


def process_dicoms(event):
    print('created')

    if 'seg' not in event.src_path:
        foldername = event.src_path
        # Pause for 15 seconds to ensure all files have been received
        time.sleep(15)
        # Read DICOM series
        Dicom_reader = DicomReaderWriter(description='Examples', arg_max=False, delete_previous_rois=False)
        print('Estimated 30 seconds, depending on number of cores present in your computer')
        Dicom_reader.walk_through_folders(foldername)
        Dicom_reader.get_images()

        image = Dicom_reader.ArrayDicom  # image array

        dicom_sitk_handle = Dicom_reader.dicom_handle
        sitk.WriteImage(dicom_sitk_handle, os.path.join(foldername, 'Image.nii'))


        ds = nib.load(foldername + '/' + 'Image.nii')
        ds2 = nip.conform(ds, (256,256, 156))

        nib.save(ds2, foldername + '/' + 'Image_resampled')

        print('file loaded')
        files = [foldername + '/' + 'Image_resampled.nii']
        working_dir = r'YOUR PATH TO '
        out = os.path.join(working_dir, 'inference')
        mkdir(out)
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

        num_labels = 6
        # Model inference
        with torch.no_grad():
            for file in files:

                net = UNesT(in_channels=1, out_channels=num_labels, num_heads=(4, 8, 16), depths=(2, 2, 8),
                            embed_dim=(128, 256, 512), patch_size=4).to(device)
                pretrained_dict = torch.load(r"YOUR PATH to WEIGHTS")
                net.load_state_dict(pretrained_dict)
                win = SlidingWindowInferer(roi_size=[128, 128, 128],
                                           sw_batch_size=1,
                                           overlap=0.5, mode='constant')
                net.eval()

                mr = nib.load(file).get_fdata()
                mr = (mr - mr.min()) / (mr.max() - mr.min())
                mr = np.expand_dims(np.array(mr).astype(np.float32), axis=0)
                mr = torch.from_numpy(mr)
                mr = mr[None, :, :, :].to(device)
                mr_seg = win(inputs=mr, network=net)
                final_seg = mr_seg.data.max(1)[1].cpu().numpy()[:, :, :].astype('uint8')

                save_im = nib.Nifti1Image(final_seg[0], affine=ds2.affine)

                resampled_seg = nip.conform(save_im, ds.shape, voxel_size=ds.header.get_zooms(), order=0)

                onehot_transform = transforms.AsDiscrete(argmax=False, to_onehot=num_labels, n_classes=num_labels,
                                                         threshold_values=False, logit_thresh=0.5)
                onehot_encoded = onehot_transform(resampled_seg.get_fdata()[None, :,:,:])

                shutil.rmtree(foldername)

                # Convert prediction to DICOM RT and save
                onehot_permute = np.array(onehot_encoded.permute(1,2,3,0))
                Dicom_reader.prediction_array_to_RT(prediction_array=np.rot90(onehot_permute[:,::-1,:], axes=(2,0))
                                                    , output_dir=r"YOUR PATH TO \Dicom_sender", ROI_Names=['Hippocampus',
                                                                                                      'Corpus_Callosum',
                                                                                                      'White_Matter_Frontal',
                                                                                                      'Temporal_Lobe',
                                                                                                      'Brainstem'])
if __name__ == "__main__":
    patterns = "*"
    ignore_patterns = ""
    ignore_directories = False
    case_sensitive = True
    my_event_handler1 = PatternMatchingEventHandler(patterns, ignore_patterns, ignore_directories, case_sensitive)
    my_event_handler1.on_created = process_dicoms
    path = r"YOUR PATH TO \Dicom_receiver"
    go_recursively = False
    my_observer = Observer()
    my_observer.schedule(my_event_handler1, path, recursive=go_recursively)

    my_event_handler2 = PatternMatchingEventHandler(patterns, ignore_patterns, ignore_directories, case_sensitive)
    my_event_handler2.on_created = send_dicoms
    path2 = r"YOUR PATH TO \Dicom_sender"
    go_recursively = True
    my_observer2 = Observer()
    my_observer2.schedule(my_event_handler2, path2, recursive=go_recursively)

    my_observer.start()
    my_observer2.start()
    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        my_observer.stop()
        my_observer.join()
        my_observer2.stop()
        my_observer2.join()