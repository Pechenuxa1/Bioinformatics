from toil.common import Toil
from toil.job import Job

def helloWorld(memory="1G", cores=1, disk="1G"):
    return f"Hello, world!"


if __name__ == "__main__":
    parser = Job.Runner.getDefaultArgumentParser()
    options = parser.parse_args()
    options.clean = "always"
    with Toil(options) as toil:
        output = toil.start(Job.wrapFn(helloWorld))
    print(output)
