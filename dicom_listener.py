from pynetdicom import AE, evt, AllStoragePresentationContexts, debug_logger, build_context
from pynetdicom.sop_class import Verification
import os
debug_logger()


def handle_store(event):
    """Saving Incoming DICOM series based on Patient ID"""

    ds = event.dataset
    root = r"YOUR PATH TO \Dicom_receiver"
    # Check if Patient ID exists in this directory and create a new dir if not
    ds.file_meta = event.file_meta
    if os.path.exists(root + '/' + ds.PatientID)==False:
        os.mkdir(root + '/' + ds.PatientID)
    # Save the dataset using the SOP Instance UID as the filename
    ds.save_as(root + '/' + ds.PatientID + '/' + ds.SOPInstanceUID +'.dcm', write_like_original=False)

    return 0x0000

handlers = [(evt.EVT_C_STORE, handle_store)]

# Initialise the Application Entity
ae = AE()
ae.add_supported_context(Verification)
ae.supported_contexts = AllStoragePresentationContexts

# Start listening to port for incoming files. Your IP should be a string, and port number an int
ae.start_server(("IP of AI server hosting model", int("Server Port Numer")), evt_handlers=handlers)

print('files transfered')
