# A SYSTEM TO COVERTLY STORE FILES IN A VFAT FILESYSTEM

## INTRODUCTION

This is a set of tools for letting you covertly put bytes on the free clusters of a FAT filesystem.
It is intended to let you hide data from hostile prying eyes.  While it is likely that skilled
data forensics people will know that *something* is (or was) on the drive, it will be difficult
for them to figure out exactly what that something was.

A good use case for this is hiding data in an SD card used in a digital camera or digital video recorder.

## COMMAND LINE

Usage is:

    python3 ./sneaky.py --block file --passphrase pw [--verbose] [--info] [--check] [--bleach] [--get file] [--put file] [--offset int] 

Options are:

* --block *file* -- always required.  Block device or file that has VFAT filesystem.
* --passphrase pw -- always required.  Give passphrase used to generate the key used to encrypt data. A zero-length passphrase will securely prompt for one.
* --verbose -- verbose output.  As much as possible operations will be quiet without --verbose.
* --info -- output information about this VFAT filesystem.
* --bleach -- fill all free clusters with random bytes.
* --check -- verify anything stored on the device.
* --get file -- get the data from the device and put it into the given file.
* --put file -- read the given file and put it onto the device
* --offset int -- offset, default of 1 which starts at the first free cluster and works forward.  -1 uses the last free cluster and works backward.

## ABOUT

This tool works by using pyfatfs to read a FAT filesystem directly and its metadata.  It looks for free clusters
on the filesystem and writes an encrypted slug of data (more about the format of the slug below) in free clusters
sequentially.  You can use the `--offset` parameter to choose a different spot in the free cluster list to read or
write the slug.  Negative values of `--offset` will write the slug backwards relative to the end of the free cluster
list.  With judicious choices you could use this feature to store multiple slugs on a given SD card.

You'll need direct access to the block device to make this work.  On Ubuntu Linux you can accomplish this by adding
yourself to the `disk` group.  On other operating systems this may be more problematic.

Since this tool quietly stores data in free clusters, any normal file writes on the filesystem are likely to destroy
whatever you store.  You can somewhat mitigate this buy using a negative `--offset`, since FAT filesystems normally
allocate clusters from the front of the free cluster list.

We are using AES encryption in CBC mode.

It needs to be emphasized that there is a nonzero chance that this tool could or would corrupt existing data on
the FAT filesystem in question.  So use with caution and care.

## SECURITY NOTES

Nothing about what is stored on any FAT filesystem is duplicated in local storage.  But if you are archiving files
you obviously had to have copies on another computer and might need to be concerned about that.

Encryption keys are generated in a cheesy fashion (SHA512) directly from the passphrase.  So choose a decent passphrase!

We use AES encryption in CBC mode.  We might use fancier modes in the future but I need to figure out where to store the
*initialization vector* and *nonce*.

Currently we have a hard-coded *initialization vector* for proof of concept.

The slug header is exactly 1024 bytes, with 17 random bytes followed by exactly 1007 bytes of ascii-encoded JSON.
We include random characters in the JSON object in order to hit exactly 1007 bytes.

A possible future implementation might use ECB for that slug header and store the *initialization vector* and *nonce*
there and use a fancier encryption mode on the rest of the slug.  How or if that would help security is unclear.

## EXAMPLES

Fill all free clusters with random bytes.  Slow but recommended before using this tool to store files.

```aiignore
python3 ./sneaky.py --block device-file --verbose --bleach
```

Put a file onto the filesystem backwards (recommended) from the end of the free list.
```aiignore
python3 ./sneaky.py --block device-file --passphrase Secret --put file.tar.gz --offset -1
```

Verify any file on the filesystem.
```aiignore
python3 ./sneaky.py --block device-file --passphrase Secret --check --offset -1
```

Get a file from the filesystem and store it locally
```aiignore
python3 ./sneaky.py --block device-file --passphrase Secret --get new_file.tar.gz --offset -1
```

## TODO

1. Some better test cases and data integrity checks to make sure we don't inadvertently trash an SD card.
2. Make verbose mode work better and more consistently for all operations.
3. Rethink how we calculate free clusters.  `sorted(keys(fs.fat))` is likely better than what we do now.
4. Consider how to do somewhat fancier encryption for our data (but not our header) with a random *iv* and *nonce*.
5. Test scripts only work on Linux.  For that matter, using this on anything but Linux is kind of problematic for a bunch of reasons.
