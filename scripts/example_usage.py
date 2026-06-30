import datetime
from dateutil.tz import tzlocal
from pynwb import NWBFile, NWBHDF5IO
from pynwb.file import Subject
from pynwb.ecephys import ElectrodeGroup
from pynwb.device import Device
import nwb_termsets

# Load the termset configuration into PyNWB
# This will update the Subject and ElectrodeGroup classes to use the termsets for validation
nwb_termsets.load_termset_config()

# Create an NWBFile
nwbfile = NWBFile(
    session_description="Example session demonstrating termsets",
    identifier="example_termsets_1",
    session_start_time=datetime.datetime.now(tzlocal()),
)

# Generate the HERD table. 
# It is then populated automatically when termsets are used in the NWBFile.
herd = nwbfile.get_external_resources()

# Create a Subject using values from the termsets
# The species must be one of the values defined in subject_species_ncbitaxon_termset.yaml
subject = Subject(
    subject_id="sub-001",
    age="P90D",
    description="Example subject",
    species="Mus musculus",  # This is validated against the NCBITaxon termset
    sex="M",
)

nwbfile.subject = subject

herd.add_ref_termset(container=subject,
                     attribute='species',
                     termset=subject.species.termset,
                     key=subject.species.value)

# Create a Device
device = Device(name="Device1")
nwbfile.add_device(device)

# Create an ElectrodeGroup using values from the termsets
# The location must be one of the values defined in brain_region_uberon_termset.yaml
electrode_group = ElectrodeGroup(
    name="ElectrodeGroup1",
    description="An example electrode group",
    location="cortical visual area",  # This is validated against the UBERON termset
    device=device,
)

nwbfile.add_electrode_group(electrode_group)

herd.add_ref_termset(container=electrode_group,
                     attribute='location',
                     termset=electrode_group.location.termset,
                     key=electrode_group.location.value)

# Write the file
filename = "example_termsets.nwb"
with NWBHDF5IO(filename, "w") as io:
    io.write(nwbfile)

print(f"Successfully created {filename} with validated termset values.")

# Read the file back to verify
with NWBHDF5IO(filename, "r") as io:
    read_nwbfile = io.read()
    print(f"Read subject species: {read_nwbfile.subject.species.value}")
    print(f"Read electrode group location: {read_nwbfile.electrode_groups['ElectrodeGroup1'].location.value}")
    
    # Print the generated HERD table
    if read_nwbfile.external_resources is not None:
        print("\nGenerated HERD table (external_resources):")
        print(read_nwbfile.external_resources.to_dataframe())
    else:
        print("\nError: HERD table (external_resources) was not generated.")
