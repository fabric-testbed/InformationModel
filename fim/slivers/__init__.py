#
# initialize the catalogs
from fim.slivers.component_catalog import ComponentCatalog
from fim.slivers.instance_catalog import InstanceCatalog

ComponentCatalog().populate_catalog_models_and_types()
InstanceCatalog()