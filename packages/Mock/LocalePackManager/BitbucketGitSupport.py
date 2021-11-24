import os.path
import logging
import subprocess
import polib

from .LocalePackRepository import LocalePackRepositoryFactory, LocalePackRepository

##----------------------------------------------------------------##
class BitbucketGitRepositoryFactory( LocalePackRepositoryFactory ):
	def getServiceName( self ):
		return 'bitbucket_git'

	def create( self, packAssetNode, localPath, repoURL, repoBranch ):
		repo = BitbucketGitRepository( packAssetNode, localPath, repoURL, repoBranch )
		return repo

##----------------------------------------------------------------##
class BitbucketGitRepository( LocalePackRepository ):
	def onPull( self ):
		url = self.repoURL
		cwd = self.localPath
		branch = self.repoBranch

		# Undo local changes
		remote = "origin"
		if branch:
			remote += "/" + branch

		if os.path.isdir( cwd + '/.git' ): #fetch
			command = ["git", "fetch", "--all"]
			_execute(command, cwd)
			
			command = ["git", "reset", "--hard", remote]
			code, output, error = _execute(command, cwd)
			if code != 0:
				raise Exception(str(error))
			logging.debug("Git: Repository at " + url + " updated.")

		else: #clone
			command = ["git", "clone", url, cwd]
			code, output, error = _execute(command)

			if code != 0:
				raise Exception(str(error))

			logging.debug("Git: Repository at " + url + " cloned.")

		#check bare
		command = ["git", "rev-parse", "--is-bare-repository"]
		code, output, error = _execute(command, cwd)
		isbare = 'true' in output

		if branch:
			command = ["git", "checkout" ]
			if isbare:
				command += [ '-B' ]
			command += [branch]
			code, output, error = _execute(command, cwd)

			if code != 0:
				raise Exception(str(error))

			logging.debug("Git: Branch " + branch + " checked out.")


	def onPush( self ):
		url = self.repoURL
		cwd = self.localPath
		branch = self.repoBranch
		message = 'update from Gii'

		logging.debug("Git: Commit to repository.")

		# Embed git identity info into commands
		git_cmd = ['git', '-c', 'user.name=Gii', '-c',
				   'user.email=info@pixpil.com']

		# Add new and remove missing paths
		_execute(git_cmd + ['add', '-A', '--', cwd], cwd)

		# Commit
		commit = git_cmd + ['commit', '-m', message ]
		code, output, error = _execute(commit, cwd)
		if code != 0 and len(error):
			raise Exception(str(error))

		# Push
		push_target = 'HEAD'
		if branch:
			push_target = branch

		push = ["git", "push", url, push_target]
		code, output, error = _execute(push, cwd)
		if code != 0:
			raise Exception(str(error))

		if 'Everything up-to-date' in error:
			print('no changes.')

		logging.info(message)


BitbucketGitRepositoryFactory().register()
##----------------------------------------------------------------##

def _execute(command, cwd=None, env=None):
	try:
		st = subprocess.PIPE
		proc = subprocess.Popen(
			args=command, stdout=st, stderr=st, stdin=st, cwd=cwd, env=env)

		(output, error) = proc.communicate()
		code = proc.returncode
		return code, output, error

	except OSError as error:
		return -1, "", error
