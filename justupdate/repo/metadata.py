import os
import logging
import json
from justupdate.core.base import JustUpdateConstants
from justupdate.core import data_manager

from justupdate.repo.version import Version

class MetaDataChannel():
	stable = 1
	beta = 2
	alpha = 3

class UnknownMetaDataError(ValueError):
	pass

class MetaData():
	def __init__(self, platform):
		self.platform = platform
		self._metadata = {}
	
	def add_metadata(self, filename, checksum, version):
		""" filename is the name of the executable created with commit, checksum is the sha512 checksum and version is the version number"""
		md = {"filename": filename, "checksum": checksum, "version":version}
		logging.debug(f"Metadata: {md}.")
		self._metadata[version] = md
		return self
	
	def get_metadata_for_version(self, version):
		if version not in self._metadata:
			raise UnknownMetaDataError(f"Metadata for version {version} on platform {self.platform} does not exist.")
		return self._metadata[version]
	
	def get_newest(self, channel):
		if channel == MetaDataChannel.ALPHA:
			return self._get_newest_alpha()
		if channel == MetaDataChannel.BETA:
			return self._get_newest_beta()
		if channel == MetaDataChannel.STABLE:
			return self._get_newest_stable()
		
	def _get_newest_alpha(self):
		v1 = Version("0.0.0a0") # the lowest version you can go.
		for version_key in self._metadata.keys():
			v2 = Version(version_key)
			if v2.is_alpha == False: # This version is not an alpha.
				continue
			if v2 > v1:
				v1 = v2
		if v1 == Version("0.0.0a0"): # If the version is still the same (no builds on this channel yet).
			return None
		return v1.to_string()
	
	def _get_newest_beta(self):
		v1 = Version("0.0.0b0") # the lowest version you can go.
		for version_key in self._metadata.keys():
			v2 = Version(version_key)
			if v2.is_beta == False: # This version is not an alpha.
				continue
			if v2 > v1:
				v1 = v2
		if v1 == Version("0.0.0b0"): # If the version is still the same (no builds on this channel yet).
			return None
		return v1.to_string()
	
	def _get_newest_stable(self):
		v1 = Version("0.0.0") # the lowest version you can go.
		for version_key in self._metadata.keys():
			v2 = Version(version_key)
			if v2.is_stable == False: # This version is not an alpha.
				continue
			if v2 > v1:
				v1 = v2
		if v1 == Version("0.0.0"): # If the version is still the same (no builds on this channel yet).
			return None
		return v1.to_string()
	
	def load(self):
		if os.path.isfile(os.path.join(JustUpdateConstants.REPO_FOLDER, "archive", f"metadata-{self.platform}.ju")) == False and os.path.isfile(os.path.join(JustUpdateConstants.REPO_FOLDER, "deploy", f"metadata-{self.platform}.ju")) == False:
			logging.debug(f"No metadata for platform {self.platform} found.")
			return {}
		
		# ok the metadata file most exist. Try to load it.
		# first see if there's one in deploy, if not, go for the one in archive.
		data = b""
		try:
			data = data_manager.open_file(os.path.join(JustUpdateConstants.REPO_FOLDER, "deploy", f"metadata-{self.platform}.ju"), "rb")
		except FileNotFoundError:
			data = data_manager.open_file(os.path.join(JustUpdateConstants.REPO_FOLDER, "archive", f"metadata-{self.platform}.ju"), "rb")
		data = data_manager.decompress(data)
		data = json.loads(data)
		return data
	
	def save(self):
		if os.path.isdir(os.path.join(JustUpdateConstants.REPO_FOLDER, "deploy")) == False:
			os.makedirs(os.path.join(JustUpdateConstants.REPO_FOLDER, "deploy"))
		data = json.dumps(self._metadata)
		data = data_manager.compress(data)
		f = open(os.path.join(JustUpdateConstants.REPO_FOLDER, "deploy", f"metadata-{self.platform}.ju"), "wb")
		f.write(data)
		f.close()
		return self
